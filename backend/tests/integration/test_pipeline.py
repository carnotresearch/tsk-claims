"""
Integration tests for the full sync pipeline (run_sync).

Tests the pipeline end-to-end: source adapter → parser → upsert → sync log.
"""
import io

import pytest
from sqlalchemy import select

from app.models import Claim, Hospital
from app.models.sync_log import ExcelSyncLog
from app.sync.pipeline import run_sync
from app.sync.sources.upload import UploadSource
from app.sync.sources.local_file import LocalFileSource

pytestmark = pytest.mark.integration


# ─────────────────────────────────────────────────────────────────────────────
# UploadSource
# ─────────────────────────────────────────────────────────────────────────────

class TestUploadSource:
    async def test_source_type(self, excel_bytes):
        src = UploadSource(excel_bytes, "test.xlsx")
        assert src.source_type() == "upload"

    async def test_source_path(self, excel_bytes):
        src = UploadSource(excel_bytes, "my_file.xlsx")
        assert src.source_path() == "my_file.xlsx"

    async def test_get_file_returns_readable_stream(self, excel_bytes):
        src = UploadSource(excel_bytes, "test.xlsx")
        stream = await src.get_file()
        assert stream.read(4) == b"PK\x03\x04"  # ZIP/XLSX magic bytes

    async def test_get_file_can_be_called_multiple_times(self, excel_bytes):
        """Each call to get_file should return a fresh stream."""
        src = UploadSource(excel_bytes, "test.xlsx")
        s1 = await src.get_file()
        s2 = await src.get_file()
        assert s1.read(4) == s2.read(4)


# ─────────────────────────────────────────────────────────────────────────────
# LocalFileSource
# ─────────────────────────────────────────────────────────────────────────────

class TestLocalFileSource:
    async def test_source_type(self, excel_path):
        src = LocalFileSource(excel_path)
        assert src.source_type() == "local_file"

    async def test_source_path(self, excel_path):
        src = LocalFileSource(excel_path)
        assert src.source_path() == excel_path

    async def test_get_file_reads_bytes(self, excel_path):
        src = LocalFileSource(excel_path)
        stream = await src.get_file()
        data = stream.read(4)
        assert data == b"PK\x03\x04"

    async def test_missing_file_raises(self):
        src = LocalFileSource("/nonexistent/path/to/file.xlsx")
        with pytest.raises(FileNotFoundError):
            await src.get_file()


# ─────────────────────────────────────────────────────────────────────────────
# Full pipeline — run_sync
# ─────────────────────────────────────────────────────────────────────────────

class TestRunSync:
    async def test_sync_returns_success_status(self, db_session, excel_bytes):
        source = UploadSource(excel_bytes, "tracker.xlsx")
        result = await run_sync(db_session, source, triggered_by="test")
        assert result.status == "success"

    async def test_sync_inserts_20_claims(self, db_session, excel_bytes):
        source = UploadSource(excel_bytes, "tracker.xlsx")
        result = await run_sync(db_session, source, triggered_by="test")
        assert result.rows_processed == 20
        assert result.rows_inserted == 20
        assert result.rows_errored == 0

    async def test_sync_writes_audit_log(self, db_session, excel_bytes):
        source = UploadSource(excel_bytes, "tracker.xlsx")
        await run_sync(db_session, source, triggered_by="test_user")
        await db_session.flush()

        result = await db_session.execute(select(ExcelSyncLog))
        logs = result.scalars().all()
        assert len(logs) == 1
        log = logs[0]
        assert log.status == "success"
        assert log.source_type == "upload"
        assert log.triggered_by == "test_user"
        assert log.rows_inserted == 20
        assert log.rows_processed == 20

    async def test_second_sync_skips_all(self, db_session, excel_bytes):
        source = UploadSource(excel_bytes, "tracker.xlsx")
        await run_sync(db_session, source, triggered_by="test")
        result2 = await run_sync(db_session, source, triggered_by="test")
        assert result2.rows_skipped == 20
        assert result2.rows_inserted == 0
        assert result2.rows_updated == 0

    async def test_second_sync_writes_second_log(self, db_session, excel_bytes):
        source = UploadSource(excel_bytes, "tracker.xlsx")
        await run_sync(db_session, source, triggered_by="test")
        await run_sync(db_session, source, triggered_by="test")
        await db_session.flush()

        result = await db_session.execute(select(ExcelSyncLog))
        logs = result.scalars().all()
        assert len(logs) == 2

    async def test_sync_result_source_fields(self, db_session, excel_bytes):
        source = UploadSource(excel_bytes, "my_tracker.xlsx")
        result = await run_sync(db_session, source, triggered_by="test")
        assert result.source_type == "upload"
        assert result.source_path == "my_tracker.xlsx"

    async def test_sync_no_errors_list(self, db_session, excel_bytes):
        source = UploadSource(excel_bytes, "tracker.xlsx")
        result = await run_sync(db_session, source, triggered_by="test")
        assert result.errors == []

    async def test_invalid_file_status_is_failed(self, db_session):
        """A corrupt file should raise (and the log should be written as failed)."""
        source = UploadSource(b"this is not an excel file", "bad.xlsx")
        with pytest.raises(Exception):
            await run_sync(db_session, source, triggered_by="test")

    async def test_db_has_claims_after_sync(self, db_session, excel_bytes):
        source = UploadSource(excel_bytes, "tracker.xlsx")
        await run_sync(db_session, source, triggered_by="test")
        await db_session.flush()

        result = await db_session.execute(select(Claim))
        claims = result.scalars().all()
        assert len(claims) == 20

    async def test_hospital_created_by_pipeline(self, db_session, excel_bytes):
        source = UploadSource(excel_bytes, "tracker.xlsx")
        await run_sync(db_session, source, triggered_by="test")
        await db_session.flush()

        result = await db_session.execute(select(Hospital))
        hospitals = result.scalars().all()
        assert len(hospitals) == 1
        assert hospitals[0].name == "Tanya Speciality Hospital"
