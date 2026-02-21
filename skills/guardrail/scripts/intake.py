"""
Guardrail Intake — quarantine an external asset before any review or execution.

Usage:
    from intake import intake_asset
    result = intake_asset("/path/to/skill_dir_or_file")
"""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
import time
from pathlib import Path
from typing import Literal

QUARANTINE_ROOT = Path.home() / ".evoclaw" / "quarantine"
BLACKLIST_FILE  = QUARANTINE_ROOT / "blacklist.json"
APPROVED_FILE   = QUARANTINE_ROOT / "approved.json"
INTAKE_LOG      = QUARANTINE_ROOT / "intake.log"

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_dirs() -> None:
    QUARANTINE_ROOT.mkdir(parents=True, exist_ok=True)


def _load_json_list(path: Path) -> list[str]:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return []
    return []


def _save_json_list(path: Path, data: list[str]) -> None:
    path.write_text(json.dumps(sorted(set(data)), indent=2))


def _compute_sha256(path: Path) -> str:
    """SHA256 of a file, or XOR-combined SHA256 of all files in a directory."""
    h = hashlib.sha256()
    if path.is_file():
        h.update(path.read_bytes())
    else:
        for f in sorted(path.rglob("*")):
            if f.is_file():
                h.update(f.read_bytes())
    return h.hexdigest()


def _log_event(event: dict) -> None:
    INTAKE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with INTAKE_LOG.open("a") as fh:
        fh.write(json.dumps(event) + "\n")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

IntakeStatus = Literal["quarantined", "blacklisted", "already_approved"]


def intake_asset(
    source: str | Path,
    asset_name: str | None = None,
    asset_type: str = "unknown",
    source_url: str | None = None,
) -> dict:
    """
    Ingest an external asset into quarantine.

    Parameters
    ----------
    source      : Local path to file or directory.
    asset_name  : Human-readable name (defaults to source basename).
    asset_type  : e.g. "ClawHub skill", "EvoMap capsule", "manual".
    source_url  : Optional origin URL for metadata.

    Returns
    -------
    {
        "asset_id": "<sha256>",
        "status":   "quarantined" | "blacklisted" | "already_approved",
        "path":     "<quarantine dir>",   # only when quarantined
    }
    """
    _ensure_dirs()
    source = Path(source)
    if not source.exists():
        raise FileNotFoundError(f"Source not found: {source}")

    asset_id = _compute_sha256(source)
    name     = asset_name or source.name
    ts       = int(time.time())

    # --- blacklist check ---
    blacklist = _load_json_list(BLACKLIST_FILE)
    if asset_id in blacklist:
        event = {"ts": ts, "asset_id": asset_id, "name": name, "status": "blacklisted"}
        _log_event(event)
        log.warning("Blocked — asset_id %s is blacklisted.", asset_id)
        return {"asset_id": asset_id, "status": "blacklisted"}

    # --- already-approved check ---
    approved = _load_json_list(APPROVED_FILE)
    if asset_id in approved:
        event = {"ts": ts, "asset_id": asset_id, "name": name, "status": "already_approved"}
        _log_event(event)
        log.info("Asset %s already approved — skipping review.", asset_id)
        return {"asset_id": asset_id, "status": "already_approved"}

    # --- quarantine ---
    dest = QUARANTINE_ROOT / asset_id
    raw  = dest / "raw"
    dest.mkdir(parents=True, exist_ok=True)
    raw.mkdir(exist_ok=True)

    if source.is_dir():
        shutil.copytree(source, raw / source.name, dirs_exist_ok=True)
    else:
        shutil.copy2(source, raw / source.name)

    metadata = {
        "asset_id":   asset_id,
        "name":       name,
        "asset_type": asset_type,
        "source_url": source_url,
        "received_at": ts,
    }
    (dest / "metadata.json").write_text(json.dumps(metadata, indent=2))

    event = {"ts": ts, "asset_id": asset_id, "name": name, "status": "quarantined", "path": str(dest)}
    _log_event(event)
    log.info("Quarantined %s → %s", name, dest)
    return {"asset_id": asset_id, "status": "quarantined", "path": str(dest)}
