from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.claim import Claim
    from app.models.user import User


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(255))
    rohini_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────
    claims: Mapped[list["Claim"]] = relationship("Claim", back_populates="hospital")
    users: Mapped[list["User"]] = relationship("User", back_populates="hospital")

    def __repr__(self) -> str:
        return f"<Hospital id={self.id} name={self.name!r}>"
