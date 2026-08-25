"""
GoogleDriveSource — stub for future Google Drive integration.

To activate:
1. pip install google-api-python-client google-auth
2. Create a service account with Drive read access
3. Set GOOGLE_DRIVE_FILE_ID and GOOGLE_SERVICE_ACCOUNT_JSON in .env
4. Implement get_file() using the Drive API

Reference:
  https://developers.google.com/drive/api/v3/manage-downloads
"""
from typing import BinaryIO

from app.sync.base import ExcelSource


class GoogleDriveSource(ExcelSource):
    def __init__(self, file_id: str, credentials_json: str) -> None:
        self._file_id = file_id
        self._credentials_json = credentials_json

    async def get_file(self) -> BinaryIO:
        raise NotImplementedError(
            "GoogleDriveSource is not yet implemented. "
            "See app/sync/sources/google_drive.py for instructions."
        )

    def source_type(self) -> str:
        return "google_drive"

    def source_path(self) -> str:
        return f"gdrive://{self._file_id}"
