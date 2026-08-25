"""
NetworkShareSource — stub for future SMB/NFS network share integration.

To activate:
1. pip install smbprotocol  (for Windows/Samba shares)
   or mount the share as a Docker volume and use LocalFileSource instead
2. Implement get_file() using smbprotocol or direct mount path

Reference:
  https://github.com/jborean93/smbprotocol
"""
from typing import BinaryIO

from app.sync.base import ExcelSource


class NetworkShareSource(ExcelSource):
    def __init__(self, smb_path: str, username: str = "", password: str = "") -> None:
        self._smb_path = smb_path
        self._username = username
        self._password = password

    async def get_file(self) -> BinaryIO:
        raise NotImplementedError(
            "NetworkShareSource is not yet implemented. "
            "For SMB/NFS shares mounted as Docker volumes, use LocalFileSource instead."
        )

    def source_type(self) -> str:
        return "network_share"

    def source_path(self) -> str:
        return self._smb_path
