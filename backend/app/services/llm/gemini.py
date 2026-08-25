"""
Google Gemini LLM provider for text-to-SQL generation and result analysis.
"""
from __future__ import annotations

import json
import re

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from app.services.llm.base import LLMProvider


_SQL_FENCE_RE = re.compile(r"```(?:sql)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)

_ANALYSIS_SYSTEM = """
You are a helpful data analyst for a hospital cashless claims management system.
You will be given a user question, the SQL query that was run, and the query results.
Write a clear, concise natural-language answer that directly addresses the question.
- Use ₹ for Indian Rupee amounts and format large numbers readably (e.g. ₹2.5L, ₹1.2Cr).
- Highlight key figures, patterns, or outliers.
- If the result is empty, say so clearly and suggest why.
- Keep the response concise — 2-5 sentences unless detail is needed.
- Do NOT repeat the SQL or mention technical details unless relevant.
""".strip()


def _extract_sql(text: str) -> str:
    """Strip markdown fences if the model wrapped its answer in them."""
    m = _SQL_FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        genai.configure(api_key=api_key)
        self._model_name = model
        self._sql_cfg = GenerationConfig(temperature=0.05, max_output_tokens=1024)
        self._ans_cfg = GenerationConfig(temperature=0.3, max_output_tokens=512)

    async def generate_sql(
        self,
        system_prompt: str,
        conversation: list[dict[str, str]],
        user_message: str,
    ) -> str:
        model = genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_prompt,
            generation_config=self._sql_cfg,
        )

        history = []
        for turn in conversation:
            role = "model" if turn["role"] == "assistant" else "user"
            history.append({"role": role, "parts": [turn["content"]]})

        chat = model.start_chat(history=history)
        response = await chat.send_message_async(user_message)
        return _extract_sql(response.text)

    async def generate_answer(
        self,
        user_question: str,
        sql: str,
        rows: list[dict],
    ) -> str:
        model = genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=_ANALYSIS_SYSTEM,
            generation_config=self._ans_cfg,
        )
        # Truncate rows sent to LLM to avoid token limits
        preview = rows[:50]
        prompt = (
            f"Question: {user_question}\n\n"
            f"SQL executed:\n{sql}\n\n"
            f"Results ({len(rows)} row(s) total, showing up to 50):\n"
            f"{json.dumps(preview, default=str, indent=2)}"
        )
        response = await model.generate_content_async(prompt)
        return response.text.strip()
