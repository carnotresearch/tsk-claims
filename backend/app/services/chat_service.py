"""
Chat service: orchestrates LLM text-to-SQL and DB query execution.

Flow per message:
  1. Load prior conversation turns from DB.
  2. Ask the LLM provider to generate a SELECT statement.
  3. Validate (must be SELECT).
  4. Execute against the DB (scoped to user's hospital if applicable).
  5. Persist user + assistant messages.
  6. Return assistant message.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.chat import ChatMessage, ChatSession
from app.services.llm.base import LLMProvider

log = logging.getLogger(__name__)

_SELECT_RE = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
_MAX_ROWS = 500

# ── Schema context given to the LLM ──────────────────────────────────────────
_SCHEMA_PROMPT = """
You are a PostgreSQL expert for a hospital cashless claims management system.
Your ONLY job is to convert the user's question into a valid SQL SELECT statement.

DATABASE SCHEMA (key columns):

TABLE: claims
  id, hospital_id (FK→hospitals), hsk_ref_id, month_label (e.g. "Apr-26")
  patient_name, insured_name, employee_code, corporate_name
  date_admission (DATE), date_discharge (DATE), los_days (INT, length of stay in days)
  payer_type (TPA / Insurer / Govt / Self-funded)
  tpa_name, insurer_name, policy_no, policy_type
  preauth_requested_amt, preauth_approved_amt, preauth_tat (days)
  final_claimed_amt  ← amount billed by hospital
  final_bill_approved_amt  ← amount approved by insurer
  hospital_discount, patient_paid_amt
  submission_date (DATE), submission_tat (days)
  query_raised (BOOL), query_raised_date, query_response_date, query_resolution_tat (days)
  settlement_date (DATE), settled_amt, tds_amt
  deduction_amt  ← computed: max(approved - (settled+tds), 0)
  payment_received_date (DATE), payment_received_amt, payment_mode, payment_tat (days)
  outstanding_amt  ← amount still owed
  ageing_days (INT), ageing_bucket (0-30 / 31-60 / 61-90 / 90+)
  final_claim_status, denial_reason, insurer_comments, hospital_remarks
  created_at, updated_at

TABLE: hospitals
  id, name, location, rohini_id

TABLE: query_denials
  id, claim_id (FK→claims), denial_type, denial_reason, denial_date,
  response_submitted, response_date, appeal_filed, resolved

RULES:
1. Return ONLY a valid SQL SELECT statement — no explanation, no markdown.
2. Never use INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, or any write operation.
3. Always alias aggregate columns (e.g. SUM(...) AS total_billed).
4. Limit results to {max_rows} rows unless the user asks for all.
{scope_rule}
""".strip()


def _build_system_prompt(hospital_id: int | None) -> str:
    if hospital_id is not None:
        scope = f"5. This user belongs to hospital_id={hospital_id}. ALWAYS add WHERE hospital_id={hospital_id} (or AND hospital_id={hospital_id}) to every query that references the claims table."
    else:
        scope = "5. This user is an admin and can query all hospitals."
    return _SCHEMA_PROMPT.format(max_rows=_MAX_ROWS, scope_rule=scope)


async def _load_history(db: AsyncSession, session_id: int) -> list[dict[str, str]]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id)
    )
    msgs = result.scalars().all()
    return [{"role": m.role, "content": m.content} for m in msgs]


async def _run_query(db: AsyncSession, sql: str) -> list[dict[str, Any]]:
    """Execute a validated SELECT and return rows as list of dicts."""
    result = await db.execute(text(sql))
    cols = list(result.keys())
    rows = result.fetchmany(_MAX_ROWS)
    return [{c: v for c, v in zip(cols, row)} for row in rows]


async def handle_message(
    db: AsyncSession,
    session: ChatSession,
    user_content: str,
    llm: LLMProvider,
    hospital_id: int | None,
) -> ChatMessage:
    """
    Process one user message: generate SQL → execute → save messages → return assistant message.
    """
    history = await _load_history(db, session.id)
    system_prompt = _build_system_prompt(hospital_id)

    # Generate SQL
    try:
        sql = await llm.generate_sql(system_prompt, history, user_content)
        log.info("chat session=%d generated SQL: %s", session.id, sql)
    except Exception as exc:
        log.warning("LLM call failed: %s", exc)
        sql = None
        user_msg = ChatMessage(session_id=session.id, role="user", content=user_content)
        db.add(user_msg)
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=f"The AI service is unavailable right now. Please check that GEMINI_API_KEY is set correctly. Error: {exc}",
        )
        db.add(assistant_msg)
        await db.flush()
        return assistant_msg

    result_rows: list[dict[str, Any]] | None = None
    answer_content: str

    if not _SELECT_RE.match(sql):
        answer_content = (
            "I could not generate a valid SQL query for that question. "
            "Please rephrase or ask about claims data."
        )
        sql = None
    else:
        try:
            result_rows = await _run_query(db, sql)
        except Exception as exc:
            log.warning("SQL execution failed: %s", exc)
            answer_content = f"I ran into an error executing the query: {exc}"
            result_rows = None
        else:
            # Step 2 — ask the LLM to analyse the results in plain English
            try:
                answer_content = await llm.generate_answer(user_content, sql, result_rows)
            except Exception as exc:
                log.warning("LLM analysis failed: %s", exc)
                # Fallback to a simple count summary so the user still gets something
                answer_content = (
                    f"Query returned {len(result_rows)} row(s)."
                    if result_rows
                    else "The query returned no results."
                )

    # Persist user message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=user_content,
    )
    db.add(user_msg)

    # Persist assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer_content,
        sql_generated=sql,
        result_rows=result_rows,
    )
    db.add(assistant_msg)
    await db.flush()
    return assistant_msg
