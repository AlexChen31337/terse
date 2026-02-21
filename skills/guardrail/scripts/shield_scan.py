"""
Shield Scan — static analysis of a quarantined asset.

Usage:
    from shield_scan import scan_asset
    result = scan_asset("abc123def456...")
"""
from __future__ import annotations

import json
import re
from pathlib import Path

QUARANTINE_ROOT  = Path.home() / ".evoclaw" / "quarantine"
CONFIG_DIR       = Path(__file__).parent.parent / "config"
SCAN_RULES_FILE  = CONFIG_DIR / "scan_rules.json"
ALLOWLIST_FILE   = CONFIG_DIR / "domain_allowlist.json"

SCORE_THRESHOLDS = {"approve": 30, "reject": 80}   # <30 → approve, ≥80 → auto-reject

SCANNABLE_EXTENSIONS = {".py", ".js", ".ts", ".sh", ".bash", ".toml", ".yaml", ".yml", ".json"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_rules() -> list[dict]:
    return json.loads(SCAN_RULES_FILE.read_text())


def _load_allowlist() -> list[str]:
    return json.loads(ALLOWLIST_FILE.read_text()).get("allowed_domains", [])


def _scan_file(path: Path, rules: list[dict], allowlist: list[str]) -> list[dict]:
    """Return list of findings for a single file."""
    findings = []
    try:
        content = path.read_text(errors="replace")
    except Exception:
        return findings

    for rule in rules:
        if re.search(rule["pattern"], content, re.IGNORECASE):
            # Suppress network rule if only allowlisted domains appear
            if rule["id"] == "network":
                domains_in_file = re.findall(r"https?://([^/'\"\s]+)", content)
                if domains_in_file and all(d in allowlist for d in domains_in_file):
                    continue
            findings.append({
                "rule_id":     rule["id"],
                "description": rule["description"],
                "score":       rule["score"],
                "file":        str(path),
            })
    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_asset(asset_id: str) -> dict:
    """
    Run static analysis on a quarantined asset.

    Returns
    -------
    {
        "asset_id":       str,
        "scan_score":     int,          # 0–100+ (capped at 100 in recommendation)
        "findings":       list[dict],
        "recommendation": "approve" | "review" | "reject",
    }
    Written to quarantine/<asset_id>/review.json.
    """
    dest = QUARANTINE_ROOT / asset_id
    raw  = dest / "raw"
    if not raw.exists():
        raise FileNotFoundError(f"No quarantine dir for asset_id {asset_id}")

    rules     = _load_rules()
    allowlist = _load_allowlist()
    findings: list[dict] = []

    for f in sorted(raw.rglob("*")):
        if f.is_file() and f.suffix in SCANNABLE_EXTENSIONS:
            findings.extend(_scan_file(f, rules, allowlist))

    # Deduplicate by rule_id (keep highest score per rule)
    seen: dict[str, dict] = {}
    for finding in findings:
        rid = finding["rule_id"]
        if rid not in seen or finding["score"] > seen[rid]["score"]:
            seen[rid] = finding
    unique_findings = list(seen.values())

    score = min(sum(f["score"] for f in unique_findings), 100)

    if score >= SCORE_THRESHOLDS["reject"]:
        recommendation = "reject"
    elif score >= SCORE_THRESHOLDS["approve"]:
        recommendation = "review"
    else:
        recommendation = "approve"

    review = {
        "asset_id":       asset_id,
        "scan_score":     score,
        "findings":       unique_findings,
        "recommendation": recommendation,
    }
    (dest / "review.json").write_text(json.dumps(review, indent=2))
    return review
