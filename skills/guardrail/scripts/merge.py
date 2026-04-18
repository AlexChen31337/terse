"""
Merge — copy approved asset to production and update registries.

Usage:
    from merge import merge_asset, reject_asset
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

QUARANTINE_ROOT = Path.home() / ".evoclaw" / "quarantine"
BLACKLIST_FILE  = QUARANTINE_ROOT / "blacklist.json"
APPROVED_FILE   = QUARANTINE_ROOT / "approved.json"
SKILLS_ROOT     = Path.home() / "clawd" / "skills"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json_list(path: Path) -> list[str]:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return []
    return []


def _save_json_list(path: Path, data: list[str]) -> None:
    path.write_text(json.dumps(sorted(set(data)), indent=2))


def _git_commit(workspace: Path, message: str) -> bool:
    result = subprocess.run(
        ["git", "add", "-A"],
        cwd=workspace, capture_output=True
    )
    if result.returncode != 0:
        return False
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=workspace, capture_output=True
    )
    return result.returncode == 0


def _send_telegram(message: str) -> None:
    subprocess.run(
        ["openclaw", "message", "send",
         "--channel", "telegram",
         "--to", "2069029798",
         "--message", message],
        check=False,
    )


def _append_changelog(skill_dir: Path, asset_id: str, name: str) -> None:
    changelog = skill_dir / "CHANGELOG.md"
    ts  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = f"\n## {ts} — Installed {name}\n- Guardrail approved. SHA256: `{asset_id}`\n"
    with changelog.open("a") as fh:
        fh.write(entry)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def merge_asset(asset_id: str, install_dir: Path | None = None) -> dict:
    """
    Copy approved asset from quarantine to production.

    install_dir: where to install (default: ~/clawd/skills/<asset_name>)

    Returns {"status": "merged", "path": str}
    """
    dest     = QUARANTINE_ROOT / asset_id
    raw      = dest / "raw"
    metadata = json.loads((dest / "metadata.json").read_text())
    name     = metadata.get("name", asset_id[:12])

    target = install_dir or (SKILLS_ROOT / name)
    target.mkdir(parents=True, exist_ok=True)

    # Copy raw contents into target
    for item in raw.iterdir():
        src = raw / item.name
        dst = target / item.name
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    # Update approved list
    approved = _load_json_list(APPROVED_FILE)
    approved.append(asset_id)
    _save_json_list(APPROVED_FILE, approved)

    # Changelog
    _append_changelog(target, asset_id, name)

    # Git commit
    workspace = Path.home() / "clawd"
    _git_commit(
        workspace,
        f"feat: install {name} [guardrail-approved sha256:{asset_id[:16]}]"
    )

    _send_telegram(f"✅ Merged: `{name}`\nSHA256: `{asset_id[:16]}...`\nInstalled at: `{target}`")
    return {"status": "merged", "path": str(target)}


def reject_asset(asset_id: str, reason: str = "") -> dict:
    """
    Reject an asset: add to blacklist and log reason.

    Returns {"status": "rejected"}
    """
    blacklist = _load_json_list(BLACKLIST_FILE)
    blacklist.append(asset_id)
    _save_json_list(BLACKLIST_FILE, blacklist)

    # Update review.json
    dest   = QUARANTINE_ROOT / asset_id
    if (dest / "review.json").exists():
        review = json.loads((dest / "review.json").read_text())
        review["decision"]   = "rejected"
        review["decided_at"] = int(time.time())
        review["reason"]     = reason
        (dest / "review.json").write_text(json.dumps(review, indent=2))

    metadata = {}
    if (dest / "metadata.json").exists():
        metadata = json.loads((dest / "metadata.json").read_text())
    name = metadata.get("name", asset_id[:12])

    _send_telegram(f"🚫 Rejected: `{name}`\nSHA256: `{asset_id[:16]}...`\nReason: {reason or 'none given'}")
    return {"status": "rejected"}
