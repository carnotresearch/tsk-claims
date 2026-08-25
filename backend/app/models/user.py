from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.hospital import Hospital
    from app.models.chat import ChatSession


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'hospital_user')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))

    # 'admin' → sees all hospitals; 'hospital_user' → scoped to hospital_id
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="hospital_user")

    # NULL for admin, required for hospital_user
    hospital_id: Mapped[int | None] = mapped_column(ForeignKey("hospitals.id"), index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Relationships ─────────────────────────────────────────
    hospital: Mapped["Hospital | None"] = relationship("Hospital", back_populates="users")
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="user")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
