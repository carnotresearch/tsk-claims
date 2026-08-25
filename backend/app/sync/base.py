"""
Abstract base class for Excel data sources.
Swap the source without changing any business logic.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import BinaryIO


@dataclass
class SyncResult:
    source_type: str
    source_path: str
    rows_processed: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_skipped: int = 0
    rows_errored: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.rows_errored == 0:
            return "success"
        if self.rows_errored < self.rows_processed:
            return "partial"
        return "failed"


class ExcelSource(ABC):
    """
    Implement this interface to add a new data source.

    Required:
      - get_file()    → return the Excel file as a binary stream
      - source_type() → short string identifier ('upload', 'local_file', etc.)
      - source_path() → human-readable location (filename, URL, path)
    """

    @abstractmethod
    async def get_file(self) -> BinaryIO:
        """Return the Excel workbook as a readable binary stream."""
        ...

    @abstractmethod
    def source_type(self) -> str:
        """Short identifier used in audit logs."""
        ...

    @abstractmethod
    def source_path(self) -> str:
        """Human-readable origin (filename, URL, drive path, etc.)."""
        ...
