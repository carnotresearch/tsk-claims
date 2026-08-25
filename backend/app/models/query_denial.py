from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, Date, DateTime, Numeric, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.claim import Claim


class QueryDenial(Base):
    """
    Mirrors the Query_Denial sheet — detailed query/denial tracking per claim.
    Multiple records can exist per claim (re-raised queries, appeals, etc.).
    """
    __tablename__ = "query_denials"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    claim_id: Mapped[int | None] = mapped_column(ForeignKey("claims.id"), index=True)
    hsk_ref_id: Mapped[str | None] = mapped_column(String(50), index=True)

    stage: Mapped[str | None] = mapped_column(String(100))            # Pre Auth Query / Submission / etc.
    query_raised_date: Mapped[date | None] = mapped_column(Date)
    query_reason_category: Mapped[str | None] = mapped_column(String(255))
    query_reason_desc: Mapped[str | None] = mapped_column(Text)
    action_required: Mapped[str | None] = mapped_column(Text)
    responsible_person: Mapped[str | None] = mapped_column(String(255))
    target_response_date: Mapped[date | None] = mapped_column(Date)
    response_date: Mapped[date | None] = mapped_column(Date)
    resolution_tat: Mapped[int | None] = mapped_column(Integer)

    resubmission_date: Mapped[date | None] = mapped_column(Date)
    disallowed_amt: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    disallowed_reason: Mapped[str | None] = mapped_column(Text)

    appeal_filed: Mapped[bool | None] = mapped_column(Boolean)
    appeal_date: Mapped[date | None] = mapped_column(Date)
    appeal_outcome: Mapped[str | None] = mapped_column(String(100))  # Pending / Approved / Rejected
    final_recovery: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    net_loss: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    status: Mapped[str | None] = mapped_column(String(100))
    remarks: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────
    claim: Mapped["Claim | None"] = relationship("Claim", back_populates="query_denials")

    def __repr__(self) -> str:
        return f"<QueryDenial id={self.id} claim_id={self.claim_id} stage={self.stage!r}>"
