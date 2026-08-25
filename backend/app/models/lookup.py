from datetime import datetime

from sqlalchemy import String, Integer, UniqueConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Lookup(Base):
    """
    Categorical master data from the Lookups sheet.
    Categories: payer_type, tpa_names, insurance_companies, preauth_status,
    discharge_status, submission_status, claim_status, payment_mode,
    ageing_buckets, policy_type, query_reasons, disallowed_reasons,
    submission_type, users
    """
    __tablename__ = "lookups"
    __table_args__ = (
        UniqueConstraint("category", "value", name="uq_lookups_category_value"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Lookup category={self.category!r} value={self.value!r}>"
