"""
Pipeline orchestrator — the single entry point for any sync operation.

Usage:
    from app.sync import run_sync
    from app.sync.sources import UploadSource

    source = UploadSource(file_bytes=raw_bytes, filename="tracker.xlsx")
    result = await run_sync(db, source, triggered_by="admin@hsk.local")

The pipeline:
  1. Gets the file stream from the source adapter
  2. Parses it (excel_parser)
  3. Upserts to database (upsert)
  4. Writes an audit log entry (ExcelSyncLog)
  5. Returns a SyncResult
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sync_log import ExcelSyncLog
from app.sync.base import ExcelSource, SyncResult
from app.sync.excel_parser import parse_workbook
from app.sync.upsert import upsert_workbook

logger = logging.getLogger(__name__)


async def run_sync(
    db: AsyncSession,
    source: ExcelSource,
    triggered_by: str = "system",
) -> SyncResult:
    """
    Execute a full sync from the given source into the database.
    Always writes an audit log entry regardless of success or failure.
    """
    result = SyncResult(
        source_type=source.source_type(),
        source_path=source.source_path(),
    )

    log_entry = ExcelSyncLog(
        source_type=source.source_type(),
        source_path=source.source_path(),
        triggered_by=triggered_by,
        synced_at=datetime.now(timezone.utc),
    )
    db.add(log_entry)

    try:
        logger.info(
            "Starting sync: source=%s path=%s triggered_by=%s",
            source.source_type(), source.source_path(), triggered_by,
        )

        # Step 1 — Fetch the file
        file_stream = await source.get_file()

        # Step 2 — Parse (CPU-bound but small files, runs inline)
        parsed = parse_workbook(file_stream)

        if parsed.parse_errors:
            for err in parsed.parse_errors:
                logger.warning("Parse warning: %s", err)
            result.errors.extend(parsed.parse_errors)

        # Step 3 — Upsert
        stats = await upsert_workbook(db, parsed)

        # Map stats back to result
        result.rows_processed = len(parsed.claims)
        result.rows_inserted = stats.claims_inserted
        result.rows_updated = stats.claims_updated
        result.rows_skipped = stats.claims_skipped
        result.rows_errored = stats.claims_errored
        result.errors.extend(stats.errors)

        # Step 4 — Write audit log
        log_entry.rows_processed = result.rows_processed
        log_entry.rows_inserted = result.rows_inserted
        log_entry.rows_updated = result.rows_updated
        log_entry.rows_skipped = result.rows_skipped
        log_entry.rows_errored = result.rows_errored
        log_entry.status = result.status
        if result.errors:
            log_entry.error_details = "\n".join(result.errors[:20])  # cap log size

        logger.info(
            "Sync complete: status=%s inserted=%d updated=%d skipped=%d errored=%d",
            result.status,
            result.rows_inserted,
            result.rows_updated,
            result.rows_skipped,
            result.rows_errored,
        )

    except Exception as exc:
        error_msg = f"Sync failed with unhandled error: {exc}"
        logger.error(error_msg, exc_info=True)
        result.errors.append(error_msg)
        log_entry.status = "failed"
        log_entry.error_details = error_msg
        raise

    return result
