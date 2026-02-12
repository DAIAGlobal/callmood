"""
Drive configuration loader.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class DriveConfig:
    clients_root_id: str
    service_account_file: Optional[Path] = None


def load_drive_config(
    config_path: Path = Path("config.yaml"),
    root_id_override: Optional[str] = None,
    service_account_override: Optional[str] = None,
) -> DriveConfig:
    """Loads Drive configuration from env or YAML.

    Priority: explicit override > env > config.yaml.
    """
    cfg: dict = {}
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh) or {}

    drive_section = cfg.get("drive", {}) if isinstance(cfg, dict) else {}

    root_id = (
        root_id_override
        or os.environ.get("DRIVE_CLIENTS_ROOT_ID")
        or drive_section.get("clients_root_id")
    )
    if not root_id:
        raise ValueError(
            "Drive clients_root_id missing. Set DRIVE_CLIENTS_ROOT_ID or drive.clients_root_id in config.yaml."
        )

    sa_path_raw = (
        service_account_override
        or os.environ.get("DRIVE_SERVICE_ACCOUNT_FILE")
        or drive_section.get("service_account_file")
    )
    sa_path = Path(sa_path_raw) if sa_path_raw else None

    return DriveConfig(clients_root_id=root_id, service_account_file=sa_path)
