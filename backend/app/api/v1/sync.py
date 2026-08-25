"""
Sync API — upload an Excel file or trigger sync from the server-side file.
"""
import os
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.config import get_settings
from app.core.deps import require_admin
from app.database import get_db
from app.models.sync_log import ExcelSyncLog
from app.models.user import User
from app.sync.pipeline import run_sync
from app.sync.sources.upload import UploadSource
from app.sync.sources.local_file import LocalFileSource

router = APIRouter(prefix="/sync", tags=["sync"])
settings = get_settings()


def _sync_response(result) -> dict:
    return {
        "status": result.status,
        "source": result.source_path,
        "rows_processed": result.rows_processed,
        "rows_inserted": result.rows_inserted,
        "rows_updated": result.rows_updated,
        "rows_skipped": result.rows_skipped,
        "rows_errored": result.rows_errored,
        "errors": result.errors[:10],
    }


@router.post("/upload", summary="Upload Excel file and run import")
async def upload_and_sync(
    file: Annotated[UploadFile, File(description="HSK Claims Tracker .xlsx file")],
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an updated Excel workbook and import all changes into the database.

    - Upserts claims by hsk_ref_id (insert new, update changed, skip identical).
    - Auto-creates hospital records from the Hospital Name column.
    - Returns a summary of rows inserted/updated/skipped.
    """
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel workbook (.xlsx or .xlsm)",
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    raw_bytes = await file.read()

    if len(raw_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb} MB",
        )

    # Persist the uploaded file so LocalFileSource / scheduled jobs can use it
    os.makedirs(settings.upload_dir, exist_ok=True)
    save_path = os.path.join(settings.upload_dir, "latest.xlsx")
    timestamped_path = os.path.join(
        settings.upload_dir,
        f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{file.filename}",
    )
    for path in (save_path, timestamped_path):
        with open(path, "wb") as fh:
            fh.write(raw_bytes)

    source = UploadSource(file_bytes=raw_bytes, filename=file.filename)

    try:
        result = await run_sync(db, source, triggered_by="api_upload")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {exc}",
        )

    return _sync_response(result)


@router.post("/trigger", summary="Trigger sync from server-side Excel file")
async def trigger_sync(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Admin-only: re-run the import using the latest Excel file on the server.

    The file must exist at the path configured by `EXCEL_FILE_PATH` (defaults to
    `uploads/latest.xlsx`, which is updated every time an admin uploads a file).
    """
    source = LocalFileSource(settings.excel_file_path)
    try:
        result = await run_sync(db, source, triggered_by="admin_trigger")
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No Excel file found at {settings.excel_file_path}. Upload a file first.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {exc}",
        )
    return _sync_response(result)


@router.get("/server-file", summary="Check server-side Excel file status")
async def server_file_status(
    _: User = Depends(require_admin),
):
    """Return metadata about the Excel file currently stored on the server."""
    path = settings.excel_file_path
    if not os.path.exists(path):
        return {"exists": False, "path": path}
    stat = os.stat(path)
    return {
        "exists": True,
        "path": path,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


@router.get("/logs", summary="List sync history")
async def list_sync_logs(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Return the most recent sync log entries."""
    result = await db.execute(
        select(ExcelSyncLog).order_by(desc(ExcelSyncLog.synced_at)).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "source_type": log.source_type,
            "source_path": log.source_path,
            "triggered_by": log.triggered_by,
            "synced_at": log.synced_at,
            "rows_processed": log.rows_processed,
            "rows_inserted": log.rows_inserted,
            "rows_updated": log.rows_updated,
            "rows_skipped": log.rows_skipped,
            "rows_errored": log.rows_errored,
            "status": log.status,
            "error_details": log.error_details,
        }
        for log in logs
    ]
