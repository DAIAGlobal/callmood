"""
Drive helper dataclasses.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DownloadedAudio:
    """Represents a downloaded audio and its Drive ID."""
    local_path: Path
    drive_file_id: str


@dataclass
class ClientFolders:
    """Resolved folder IDs for a client in Drive."""
    client_id: str
    audio_pendiente_id: Optional[str]
    audio_auditado_id: Optional[str]
    audio_error_id: Optional[str]
    reportes_id: Optional[str]
