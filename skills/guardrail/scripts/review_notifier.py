"""
Review Notifier — send Telegram approval card and record the decision.

Usage:
    from review_notifier import notify_and_wait, record_decision
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

QUARANTINE_ROOT = Path.home() / ".evoclaw" / "quarantine"
POLL_INTERVAL   = 30   # seconds between decision-file polls
TIMEOUT_HOURS   = 24


def _send_telegram(message: str) -> None:
    """Send a Telegram message via openclaw CLI."""
    subprocess.run(
        ["openclaw", "message", "send",
         "--channel", "telegram",
         "--to", "2069029798",
         "--message", message],
        check=False,
    )


def _build_card(asset_id: str, review: dict, metadata: dict) -> str:
    name  = metadata.get("name", asset_id[:12])
    atype = metadata.get("asset_type", "unknown")
    score = review.get("scan_score", "?")
    rec   = review.get("recommendation", "?")
    findings = review.get("findings", [])

    icon = {"approve": "✅", "review": "⚠️", "reject": "🔴"}.get(rec, "❓")

    lines = [
        f"🔍 *Asset Review Required*",
        f"",
        f"Name: `{name}`",
        f"Type: {atype}",
        f"SHA256: `{asset_id[:16]}...`",
        f"",
        f"Shield Scan: {icon} Score {score}/100",
    ]
    if findings:
        lines.append("Findings:")
        for f in findings[:6]:
            lines.append(f"  • {f['description']} (+{f['score']})")
        if len(findings) > 6:
            lines.append(f"  • ...and {len(findings)-6} more")
    else:
        lines.append("  No issues found.")

    lines += [
        f"",
        f"To decide, reply:",
        f"  `APPROVE {asset_id[:12]}`",
        f"  `REJECT {asset_id[:12]}`",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def notify_review(asset_id: str) -> None:
    """Send the Telegram review card for an asset."""
    dest     = QUARANTINE_ROOT / asset_id
    review   = json.loads((dest / "review.json").read_text())
    metadata = json.loads((dest / "metadata.json").read_text())
    card     = _build_card(asset_id, review, metadata)
    _send_telegram(card)


def record_decision(asset_id: str, decision: str, reason: str = "") -> None:
    """
    Persist approve/reject decision to review.json.

    decision: "approved" | "rejected"
    """
    dest   = QUARANTINE_ROOT / asset_id
    review = json.loads((dest / "review.json").read_text())
    review["decision"]    = decision
    review["decided_at"]  = int(time.time())
    review["reason"]      = reason
    (dest / "review.json").write_text(json.dumps(review, indent=2))


def wait_for_decision(asset_id: str, timeout_hours: int = TIMEOUT_HOURS) -> str:
    """
    Poll review.json until a decision is recorded or timeout expires.

    Returns "approved" | "rejected" | "timeout".
    """
    dest     = QUARANTINE_ROOT / asset_id
    deadline = time.time() + timeout_hours * 3600

    while True:
        review = json.loads((dest / "review.json").read_text())
        if "decision" in review:
            return review["decision"]
        if time.time() >= deadline:
            return "timeout"
        time.sleep(POLL_INTERVAL)
