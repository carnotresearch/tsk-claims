"""Initial schema — all tables

Revision ID: 001
Revises:
Create Date: 2026-08-24
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── hospitals ─────────────────────────────────────────────
    op.create_table(
        "hospitals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("rohini_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_hospitals_name", "hospitals", ["name"])

    # ── users ─────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('admin', 'hospital_user')", name="ck_users_role"),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_hospital_id", "users", ["hospital_id"])

    # ── claims ────────────────────────────────────────────────
    op.create_table(
        "claims",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hospital_id", sa.Integer(), nullable=False),
        # Reference & IDs
        sa.Column("hsk_ref_id", sa.String(50), nullable=True),
        sa.Column("month_label", sa.String(20), nullable=True),
        sa.Column("ihx_ref_id", sa.String(100), nullable=True),
        sa.Column("uhid", sa.String(100), nullable=True),
        sa.Column("ip_number", sa.String(100), nullable=True),
        # Patient
        sa.Column("patient_name", sa.String(255), nullable=True),
        sa.Column("patient_contact", sa.String(50), nullable=True),
        sa.Column("insured_name", sa.String(255), nullable=True),
        sa.Column("employee_code", sa.String(100), nullable=True),
        sa.Column("corporate_name", sa.String(255), nullable=True),
        # Admission & Stay
        sa.Column("date_admission", sa.Date(), nullable=True),
        sa.Column("date_discharge", sa.Date(), nullable=True),
        sa.Column("los_days", sa.Integer(), nullable=True),
        sa.Column("procedure_name", sa.String(255), nullable=True),
        sa.Column("diagnosis", sa.Text(), nullable=True),
        # Payor & Policy
        sa.Column("payer_type", sa.String(100), nullable=True),
        sa.Column("tpa_name", sa.String(255), nullable=True),
        sa.Column("insurer_name", sa.String(255), nullable=True),
        sa.Column("policy_no", sa.String(255), nullable=True),
        sa.Column("policy_type", sa.String(100), nullable=True),
        # Preauth
        sa.Column("preauth_no", sa.String(255), nullable=True),
        sa.Column("initial_claim_no", sa.String(255), nullable=True),
        sa.Column("preauth_request_date", sa.Date(), nullable=True),
        sa.Column("preauth_approval_date", sa.Date(), nullable=True),
        sa.Column("preauth_requested_amt", sa.Numeric(14, 2), nullable=True),
        sa.Column("preauth_approved_amt", sa.Numeric(14, 2), nullable=True),
        sa.Column("preauth_copay", sa.Numeric(14, 2), nullable=True),
        sa.Column("preauth_status", sa.String(100), nullable=True),
        sa.Column("preauth_tat", sa.Integer(), nullable=True),
        # Discharge / Final Bill
        sa.Column("final_bill_request_date", sa.Date(), nullable=True),
        sa.Column("final_bill_approval_date", sa.Date(), nullable=True),
        sa.Column("final_claimed_amt", sa.Numeric(14, 2), nullable=True),
        sa.Column("final_bill_approved_amt", sa.Numeric(14, 2), nullable=True),
        sa.Column("hospital_discount", sa.Numeric(14, 2), nullable=True),
        sa.Column("patient_paid_amt", sa.Numeric(14, 2), nullable=True),
        sa.Column("discharge_status", sa.String(100), nullable=True),
        sa.Column("discharge_tat", sa.Integer(), nullable=True),
        # Submission
        sa.Column("submission_type", sa.String(100), nullable=True),
        sa.Column("submission_date", sa.Date(), nullable=True),
        sa.Column("submission_tat", sa.Integer(), nullable=True),
        sa.Column("submission_status", sa.String(100), nullable=True),
        sa.Column("courier_agency", sa.String(255), nullable=True),
        sa.Column("courier_destination", sa.String(255), nullable=True),
        sa.Column("courier_dispatch_date", sa.Date(), nullable=True),
        sa.Column("courier_awb", sa.String(255), nullable=True),
        sa.Column("hospital_invoice_no", sa.String(100), nullable=True),
        # Query & Denial
        sa.Column("query_raised", sa.Boolean(), nullable=True),
        sa.Column("query_raised_date", sa.Date(), nullable=True),
        sa.Column("query_reason", sa.Text(), nullable=True),
        sa.Column("query_response_date", sa.Date(), nullable=True),
        sa.Column("query_resolution_tat", sa.Integer(), nullable=True),
        sa.Column("resubmission_date", sa.Date(), nullable=True),
        sa.Column("disallowed_amt", sa.Numeric(14, 2), nullable=True),
        sa.Column("denial_reason", sa.Text(), nullable=True),
        sa.Column("appeal_filed", sa.Boolean(), nullable=True),
        sa.Column("appeal_date", sa.Date(), nullable=True),
        # Settlement & Payment
        sa.Column("settlement_date", sa.Date(), nullable=True),
        sa.Column("settled_amt", sa.Numeric(14, 2), nullable=True),
        sa.Column("tds_amt", sa.Numeric(14, 2), nullable=True),
        sa.Column("deduction_amt", sa.Numeric(14, 2), nullable=True),
        sa.Column("utr_no", sa.String(255), nullable=True),
        sa.Column("utr_date", sa.Date(), nullable=True),
        sa.Column("payment_received_date", sa.Date(), nullable=True),
        sa.Column("payment_received_amt", sa.Numeric(14, 2), nullable=True),
        sa.Column("payment_mode", sa.String(100), nullable=True),
        sa.Column("hospital_receipt_no", sa.String(100), nullable=True),
        sa.Column("payment_tat", sa.Integer(), nullable=True),
        # Outstanding & Ageing
        sa.Column("outstanding_amt", sa.Numeric(14, 2), nullable=True),
        sa.Column("ageing_days", sa.Integer(), nullable=True),
        sa.Column("ageing_bucket", sa.String(20), nullable=True),
        # Status & Notes
        sa.Column("final_claim_status", sa.String(100), nullable=True),
        sa.Column("insurer_comments", sa.Text(), nullable=True),
        sa.Column("hospital_remarks", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
        sa.Column("last_updated_date", sa.Date(), nullable=True),
        # Metadata
        sa.Column("raw_row_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hsk_ref_id"),
    )
    op.create_index("ix_claims_hsk_ref_id", "claims", ["hsk_ref_id"])
    op.create_index("ix_claims_ihx_ref_id", "claims", ["ihx_ref_id"])
    op.create_index("ix_claims_hospital_status", "claims", ["hospital_id", "final_claim_status"])
    op.create_index("ix_claims_hospital_admission", "claims", ["hospital_id", "date_admission"])
    op.create_index("ix_claims_insurer", "claims", ["insurer_name"])
    op.create_index("ix_claims_payer_type", "claims", ["payer_type"])
    op.create_index("ix_claims_submission_date", "claims", ["submission_date"])
    op.create_index("ix_claims_settlement_date", "claims", ["settlement_date"])
    op.create_index("ix_claims_final_claim_status", "claims", ["final_claim_status"])

    # ── query_denials ─────────────────────────────────────────
    op.create_table(
        "query_denials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("claim_id", sa.Integer(), nullable=True),
        sa.Column("hsk_ref_id", sa.String(50), nullable=True),
        sa.Column("stage", sa.String(100), nullable=True),
        sa.Column("query_raised_date", sa.Date(), nullable=True),
        sa.Column("query_reason_category", sa.String(255), nullable=True),
        sa.Column("query_reason_desc", sa.Text(), nullable=True),
        sa.Column("action_required", sa.Text(), nullable=True),
        sa.Column("responsible_person", sa.String(255), nullable=True),
        sa.Column("target_response_date", sa.Date(), nullable=True),
        sa.Column("response_date", sa.Date(), nullable=True),
        sa.Column("resolution_tat", sa.Integer(), nullable=True),
        sa.Column("resubmission_date", sa.Date(), nullable=True),
        sa.Column("disallowed_amt", sa.Numeric(14, 2), nullable=True),
        sa.Column("disallowed_reason", sa.Text(), nullable=True),
        sa.Column("appeal_filed", sa.Boolean(), nullable=True),
        sa.Column("appeal_date", sa.Date(), nullable=True),
        sa.Column("appeal_outcome", sa.String(100), nullable=True),
        sa.Column("final_recovery", sa.Numeric(14, 2), nullable=True),
        sa.Column("net_loss", sa.Numeric(14, 2), nullable=True),
        sa.Column("status", sa.String(100), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_query_denials_claim_id", "query_denials", ["claim_id"])
    op.create_index("ix_query_denials_hsk_ref_id", "query_denials", ["hsk_ref_id"])

    # ── lookups ───────────────────────────────────────────────
    op.create_table(
        "lookups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("value", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category", "value", name="uq_lookups_category_value"),
    )
    op.create_index("ix_lookups_category", "lookups", ["category"])

    # ── excel_sync_log ────────────────────────────────────────
    op.create_table(
        "excel_sync_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_path", sa.String(500), nullable=True),
        sa.Column("triggered_by", sa.String(255), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("rows_processed", sa.Integer(), nullable=True),
        sa.Column("rows_inserted", sa.Integer(), nullable=True),
        sa.Column("rows_updated", sa.Integer(), nullable=True),
        sa.Column("rows_skipped", sa.Integer(), nullable=True),
        sa.Column("rows_errored", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── chat_sessions ─────────────────────────────────────────
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])

    # ── chat_messages ─────────────────────────────────────────
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sql_generated", sa.Text(), nullable=True),
        sa.Column("result_rows", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_messages_role"),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("excel_sync_log")
    op.drop_table("lookups")
    op.drop_table("query_denials")
    op.drop_table("claims")
    op.drop_table("users")
    op.drop_table("hospitals")
