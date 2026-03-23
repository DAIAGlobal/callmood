"""
Thin wrapper around Google Drive API (service account auth).
"""
from __future__ import annotations
import io
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

from .drive_types import DownloadedAudio

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME = "application/vnd.google-apps.folder"


class DriveClient:
    """Minimal Drive client for listing, download, upload, and move."""

    def __init__(self, service_account_file: Path):
        if not service_account_file:
            raise ValueError("Service account file path is required for DriveClient")
        if not Path(service_account_file).exists():
            raise FileNotFoundError(f"Service account file not found: {service_account_file}")

        creds = service_account.Credentials.from_service_account_file(
            str(service_account_file), scopes=SCOPES
        )
        # cache_discovery=False avoids warnings in googleapiclient
        self.service = build("drive", "v3", credentials=creds, cache_discovery=False)

    def list_subfolders(self, parent_id: str) -> List[Tuple[str, str]]:
        """Returns (id, name) for subfolders under parent."""
        query = f"'{parent_id}' in parents and mimeType='{FOLDER_MIME}' and trashed=false"
        try:
            resp = self.service.files().list(q=query, fields="files(id,name)").execute()
            return [(f["id"], f["name"]) for f in resp.get("files", [])]
        except HttpError as exc:
            logger.warning("[drive] list_subfolders failed: %s", exc)
            return []

    def list_files(self, parent_id: str) -> List[Tuple[str, str]]:
        """Returns (id, name) for non-folder files under parent."""
        query = (
            f"'{parent_id}' in parents and trashed=false "
            f"and mimeType!='{FOLDER_MIME}'"
        )
        try:
            resp = self.service.files().list(q=query, fields="files(id,name)").execute()
            return [(f["id"], f["name"]) for f in resp.get("files", [])]
        except HttpError as exc:
            logger.warning("[drive] list_files failed: %s", exc)
            return []

    def find_file_by_name(self, parent_id: str, name: str) -> Optional[str]:
        """Return file ID if a non-folder file with name exists under parent."""
        query = (
            f"'{parent_id}' in parents and name='{name}' and "
            f"mimeType!='{FOLDER_MIME}' and trashed=false"
        )
        try:
            resp = self.service.files().list(q=query, fields="files(id)").execute()
            files = resp.get("files", [])
            return files[0]["id"] if files else None
        except HttpError as exc:
            logger.warning("[drive] find_file_by_name failed: %s", exc)
            return None

    def find_subfolder(self, parent_id: str, name: str) -> Optional[str]:
        query = (
            f"'{parent_id}' in parents and name='{name}' and "
            f"mimeType='{FOLDER_MIME}' and trashed=false"
        )
        try:
            resp = self.service.files().list(q=query, fields="files(id)").execute()
            files = resp.get("files", [])
            return files[0]["id"] if files else None
        except HttpError as exc:
            logger.warning("[drive] find_subfolder failed: %s", exc)
            return None

    def download_files(self, folder_id: str, target_dir: Path) -> List[DownloadedAudio]:
        target_dir.mkdir(parents=True, exist_ok=True)
        items: List[DownloadedAudio] = []

        try:
            resp = self.service.files().list(
                q=(
                    f"'{folder_id}' in parents and trashed=false and "
                    f"mimeType!='{FOLDER_MIME}'"
                ),
                fields="files(id,name)",
            ).execute()
        except HttpError as exc:
            logger.warning("[drive] download_files/list failed: %s", exc)
            return items

        for f in resp.get("files", []):
            file_id = f.get("id")
            name = f.get("name") or "audio"
            dest = target_dir / name
            try:
                request = self.service.files().get_media(fileId=file_id)
                with io.FileIO(dest, mode="wb") as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        _, done = downloader.next_chunk()
                items.append(DownloadedAudio(local_path=dest, drive_file_id=file_id))
            except HttpError as exc:
                logger.warning("[drive] download failed for %s: %s", name, exc)
                if dest.exists():
                    dest.unlink(missing_ok=True)

        return items

    def upload_file(self, parent_id: str, local_path: Path) -> Optional[str]:
        metadata = {"name": local_path.name, "parents": [parent_id]}
        media = MediaFileUpload(local_path, resumable=True)
        try:
            resp = (
                self.service.files()
                .create(body=metadata, media_body=media, fields="id")
                .execute()
            )
            return resp.get("id")
        except HttpError as exc:
            logger.warning("[drive] upload failed for %s: %s", local_path, exc)
            return None

    def delete_file(self, file_id: str) -> bool:
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except HttpError as exc:
            logger.warning("[drive] delete failed for %s: %s", file_id, exc)
            return False

    def move_file(self, file_id: str, new_parent_id: str) -> bool:
        try:
            file = self.service.files().get(fileId=file_id, fields="parents").execute()
            prev_parents = ",".join(file.get("parents", []))
            self.service.files().update(
                fileId=file_id,
                addParents=new_parent_id,
                removeParents=prev_parents,
                fields="id, parents",
            ).execute()
            return True
        except HttpError as exc:
            logger.warning("[drive] move failed for %s: %s", file_id, exc)
            return False
