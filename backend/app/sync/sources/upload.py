"""
UploadSource — receives raw bytes from a multipart HTTP upload.
This is the default source for Phase 1.
"""
import io
from typing import BinaryIO

from app.sync.base import ExcelSource


class UploadSource(ExcelSource):
    def __init__(self, file_bytes: bytes, filename: str = "upload.xlsx") -> None:
        self._file_bytes = file_bytes
        self._filename = filename

    async def get_file(self) -> BinaryIO:
        return io.BytesIO(self._file_bytes)

    def source_type(self) -> str:
        return "upload"

    def source_path(self) -> str:
        return self._filename
