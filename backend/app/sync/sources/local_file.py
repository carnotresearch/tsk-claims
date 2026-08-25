"""
LocalFileSource — reads from a file path on the container filesystem.
Used with SYNC_SOURCE=local_file when the Excel is mounted as a volume
(e.g. NFS / Samba share, or a locally-mapped directory).
"""
import asyncio
import os
from typing import BinaryIO

from app.sync.base import ExcelSource


class LocalFileSource(ExcelSource):
    def __init__(self, path: str) -> None:
        self._path = path

    async def get_file(self) -> BinaryIO:
        if not os.path.exists(self._path):
            raise FileNotFoundError(f"Excel file not found at: {self._path}")
        # Run blocking file I/O in thread pool so we don't block the event loop
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, self._read)
        import io
        return io.BytesIO(data)

    def _read(self) -> bytes:
        with open(self._path, "rb") as fh:
            return fh.read()

    def source_type(self) -> str:
        return "local_file"

    def source_path(self) -> str:
        return self._path
