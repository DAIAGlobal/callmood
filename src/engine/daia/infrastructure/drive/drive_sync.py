"""
Orchestration helpers for Drive pull/push.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .drive_client import DriveClient
from .drive_config import DriveConfig
from .drive_types import ClientFolders, DownloadedAudio

logger = logging.getLogger(__name__)

REQUIRED_SUBFOLDERS = {
    "audio_pendiente",
    "audio_auditado",
    "audio_error",
    "reportes",
}


def list_clients(client: DriveClient, drive_cfg: DriveConfig) -> List[Tuple[str, str]]:
    """Lists client folders under the configured root."""
    return client.list_subfolders(drive_cfg.clients_root_id)


def resolve_client_folders(
    client: DriveClient, drive_cfg: DriveConfig, client_name: str
) -> Optional[ClientFolders]:
    """Resolve folder IDs for a given client name."""
    clients = {name: cid for cid, name in list_clients(client, drive_cfg)}
    client_id = clients.get(client_name)
    if not client_id:
        logger.warning("[drive] Client folder not found: %s", client_name)
        return None

    children = {name: cid for cid, name in client.list_subfolders(client_id)}
    missing = REQUIRED_SUBFOLDERS - set(children.keys())
    if missing:
        logger.warning("[drive] Missing subfolders for %s: %s", client_name, ", ".join(sorted(missing)))

    return ClientFolders(
        client_id=client_id,
        audio_pendiente_id=children.get("audio_pendiente"),
        audio_auditado_id=children.get("audio_auditado"),
        audio_error_id=children.get("audio_error"),
        reportes_id=children.get("reportes"),
    )


def pull_pending_audios(
    client: DriveClient,
    folders: ClientFolders,
    tmp_dir: Path,
) -> List[DownloadedAudio]:
    """Downloads pending audios for a client."""
    if not folders.audio_pendiente_id:
        logger.warning("[drive] audio_pendiente folder not configured; skipping download")
        return []
    return client.download_files(folders.audio_pendiente_id, tmp_dir)


def push_reports(
    client: DriveClient,
    folders: ClientFolders,
    report_paths: Iterable[Path],
) -> None:
    """Uploads generated reports to Drive."""
    if not folders.reportes_id:
        logger.warning("[drive] reportes folder not configured; skipping upload")
        return

    for report_path in report_paths:
        if not report_path.exists():
            logger.warning("[drive] Report file missing locally, skip upload: %s", report_path)
            continue
        # Idempotency: overwrite if same name exists
        existing_id = client.find_file_by_name(folders.reportes_id, report_path.name)
        if existing_id:
            client.delete_file(existing_id)
        client.upload_file(folders.reportes_id, report_path)


def move_audios(
    client: DriveClient,
    folders: ClientFolders,
    successes: Iterable[DownloadedAudio],
    failures: Iterable[DownloadedAudio],
) -> None:
    """Moves processed audios to their final folders."""
    success_items = list(successes)
    failure_items = list(failures)

    if folders.audio_auditado_id:
        for item in success_items:
            client.move_file(item.drive_file_id, folders.audio_auditado_id)
    elif success_items:
        logger.warning("[drive] audio_auditado folder missing; cannot move successes")

    if folders.audio_error_id:
        for item in failure_items:
            client.move_file(item.drive_file_id, folders.audio_error_id)
    elif failure_items:
        logger.warning("[drive] audio_error folder missing; cannot move failures")
