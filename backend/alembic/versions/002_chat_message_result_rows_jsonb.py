"""Change chat_messages.result_rows from Integer to JSONB

Revision ID: 002
Revises: 001
Create Date: 2026-08-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "chat_messages",
        "result_rows",
        existing_type=sa.Integer(),
        type_=JSONB(),
        existing_nullable=True,
        postgresql_using="NULL",
    )


def downgrade() -> None:
    op.alter_column(
        "chat_messages",
        "result_rows",
        existing_type=JSONB(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="NULL",
    )
