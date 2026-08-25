"""
API tests for the sync endpoints:
  POST /api/v1/sync/upload
  GET  /api/v1/sync/logs
"""
import io
import os

import pytest

pytestmark = pytest.mark.api


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _xlsx_files(raw_bytes: bytes, filename: str = "tracker.xlsx"):
    """Build a multipart upload payload."""
    return {"file": (filename, io.BytesIO(raw_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/sync/upload — happy path
# ─────────────────────────────────────────────────────────────────────────────

class TestSyncUploadHappyPath:
    async def test_upload_returns_200(self, client, excel_bytes):
        response = await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))
        assert response.status_code == 200

    async def test_upload_status_success(self, client, excel_bytes):
        data = (await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))).json()
        assert data["status"] == "success"

    async def test_upload_inserts_20_rows(self, client, excel_bytes):
        data = (await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))).json()
        assert data["rows_processed"] == 20
        assert data["rows_inserted"] == 20
        assert data["rows_errored"] == 0

    async def test_upload_no_errors(self, client, excel_bytes):
        data = (await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))).json()
        assert data["errors"] == []

    async def test_upload_response_has_all_keys(self, client, excel_bytes):
        data = (await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))).json()
        expected_keys = {
            "status", "source", "rows_processed", "rows_inserted",
            "rows_updated", "rows_skipped", "rows_errored", "errors",
        }
        assert expected_keys.issubset(set(data.keys()))

    async def test_reupload_skips_all(self, client, excel_bytes):
        """Second identical upload → 0 inserted, 20 skipped."""
        await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))
        data = (await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))).json()
        assert data["rows_skipped"] == 20
        assert data["rows_inserted"] == 0
        assert data["rows_updated"] == 0

    async def test_filename_preserved_in_response(self, client, excel_bytes):
        data = (await client.post(
            "/api/v1/sync/upload",
            files=_xlsx_files(excel_bytes, "my_claims.xlsx"),
        )).json()
        assert data["source"] == "my_claims.xlsx"


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/sync/upload — error cases
# ─────────────────────────────────────────────────────────────────────────────

class TestSyncUploadErrors:
    async def test_no_file_returns_422(self, client):
        response = await client.post("/api/v1/sync/upload")
        assert response.status_code == 422

    async def test_wrong_extension_returns_400(self, client):
        fake_csv = b"col1,col2\n1,2"
        response = await client.post(
            "/api/v1/sync/upload",
            files={"file": ("data.csv", io.BytesIO(fake_csv), "text/csv")},
        )
        assert response.status_code == 400

    async def test_txt_extension_returns_400(self, client):
        response = await client.post(
            "/api/v1/sync/upload",
            files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert response.status_code == 400

    async def test_corrupt_xlsx_returns_500(self, client):
        """Valid extension but corrupt content — parser fails."""
        corrupt = b"PK\x03\x04" + b"\x00" * 100  # looks like zip but isn't
        response = await client.post(
            "/api/v1/sync/upload",
            files={"file": ("broken.xlsx", io.BytesIO(corrupt), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code in (400, 500)

    async def test_empty_file_returns_error(self, client):
        response = await client.post(
            "/api/v1/sync/upload",
            files={"file": ("empty.xlsx", io.BytesIO(b""), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert response.status_code in (400, 422, 500)

    async def test_xlsm_extension_accepted(self, client, excel_bytes):
        """Macro-enabled workbooks (.xlsm) are also valid."""
        response = await client.post(
            "/api/v1/sync/upload",
            files=_xlsx_files(excel_bytes, "tracker.xlsm"),
        )
        # Should not be 400 (extension check passes)
        assert response.status_code != 400


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/sync/logs
# ─────────────────────────────────────────────────────────────────────────────

class TestSyncLogs:
    async def test_logs_empty_before_any_sync(self, client):
        response = await client.get("/api/v1/sync/logs")
        assert response.status_code == 200
        assert response.json() == []

    async def test_logs_has_one_entry_after_upload(self, client, excel_bytes):
        await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))
        logs = (await client.get("/api/v1/sync/logs")).json()
        assert len(logs) == 1

    async def test_logs_entry_has_expected_fields(self, client, excel_bytes):
        await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))
        log = (await client.get("/api/v1/sync/logs")).json()[0]
        expected_keys = {
            "id", "source_type", "source_path", "triggered_by",
            "synced_at", "rows_processed", "rows_inserted",
            "rows_updated", "rows_skipped", "rows_errored", "status", "error_details",
        }
        assert expected_keys.issubset(set(log.keys()))

    async def test_log_status_success(self, client, excel_bytes):
        await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))
        log = (await client.get("/api/v1/sync/logs")).json()[0]
        assert log["status"] == "success"

    async def test_log_rows_match_upload_response(self, client, excel_bytes):
        upload_resp = (await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))).json()
        log = (await client.get("/api/v1/sync/logs")).json()[0]
        assert log["rows_processed"] == upload_resp["rows_processed"]
        assert log["rows_inserted"] == upload_resp["rows_inserted"]

    async def test_two_uploads_two_logs(self, client, excel_bytes):
        await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))
        await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))
        logs = (await client.get("/api/v1/sync/logs")).json()
        assert len(logs) == 2

    async def test_logs_ordered_newest_first(self, client, excel_bytes):
        await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))
        await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))
        logs = (await client.get("/api/v1/sync/logs")).json()
        # Most recent log should have the higher id
        assert logs[0]["id"] > logs[1]["id"]

    async def test_logs_limit_param(self, client, excel_bytes):
        for _ in range(3):
            await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))
        logs = (await client.get("/api/v1/sync/logs?limit=2")).json()
        assert len(logs) == 2

    async def test_source_type_is_upload(self, client, excel_bytes):
        await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))
        log = (await client.get("/api/v1/sync/logs")).json()[0]
        assert log["source_type"] == "upload"

    async def test_triggered_by_is_api_upload(self, client, excel_bytes):
        await client.post("/api/v1/sync/upload", files=_xlsx_files(excel_bytes))
        log = (await client.get("/api/v1/sync/logs")).json()[0]
        assert log["triggered_by"] == "api_upload"
