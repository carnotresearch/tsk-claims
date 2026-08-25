from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExcelSyncLog(Base):
    """Audit trail for every Excel import operation."""
    __tablename__ = "excel_sync_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Which adapter was used
    source_type: Mapped[str | None] = mapped_column(String(50))   # upload / local_file / google_drive
    source_path: Mapped[str | None] = mapped_column(String(500))  # filename, URL, or path
    triggered_by: Mapped[str | None] = mapped_column(String(255)) # user email or 'scheduler'

    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rows_processed: Mapped[int | None] = mapped_column(Integer)
    rows_inserted: Mapped[int | None] = mapped_column(Integer)
    rows_updated: Mapped[int | None] = mapped_column(Integer)
    rows_skipped: Mapped[int | None] = mapped_column(Integer)
    rows_errored: Mapped[int | None] = mapped_column(Integer)

    # 'success' | 'partial' | 'failed'
    status: Mapped[str | None] = mapped_column(String(20))
    error_details: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<ExcelSyncLog id={self.id} status={self.status!r} at={self.synced_at}>"
