from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ChatSession(Base):
    """A named conversation thread per user."""
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", order_by="ChatMessage.created_at"
    )

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} user_id={self.user_id}>"


class ChatMessage(Base):
    """Single message inside a chat session."""
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_messages_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), nullable=False, index=True)

    role: Mapped[str] = mapped_column(String(20), nullable=False)    # user / assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sql_generated: Mapped[str | None] = mapped_column(Text)          # SQL the LLM produced
    result_rows: Mapped[list[Any] | None] = mapped_column(JSONB)     # query result rows as JSON

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} role={self.role!r}>"
