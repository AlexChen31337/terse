#!/usr/bin/env python3
"""
RSI Loop - Observer
Logs agent turn outcomes to a structured JSONL store.
Called at end of each significant task/turn to build the improvement dataset.
"""

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
OUTCOMES_FILE = DATA_DIR / "outcomes.jsonl"

# ── Task type taxonomy ─────────────────────────────────────────────────────────
TASK_TYPES = [
    "code_generation", "code_debug", "code_review",
    "architecture_design", "file_ops", "web_search",
    "memory_retrieval", "skill_creation", "cron_management",
    "api_integration", "data_analysis", "message_routing",
    "infrastructure_ops", "documentation", "general_qa",
    "trading", "monitoring", "blockchain", "unknown"
]

# ── Issue taxonomy ─────────────────────────────────────────────────────────────
ISSUE_TYPES = [
    "rate_limit", "model_fallback", "tool_error", "wrong_output",
    "incomplete_task", "context_loss", "memory_miss", "skill_gap",
    "bad_routing", "slow_response", "over_confirmation", "repeated_mistake",
    "missing_tool", "wrong_model_tier", "compaction_lost_context", "other"
]

def load_outcomes():
    if not OUTCOMES_FILE.exists():
        return []
    outcomes = []
    with open(OUTCOMES_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    outcomes.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return outcomes

def log_outcome(
    task_type: str,
    success: bool,
    quality: int,  # 1-5
    model: str = "",
    duration_ms: int = 0,
    issues: list = None,
    tags: list = None,
    notes: str = "",
    session_id: str = "",
    agent_id: str = "main",
):
    """Log a single turn outcome."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if task_type not in TASK_TYPES:
        task_type = "unknown"

    record = {
        "id": str(uuid.uuid4())[:8],
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "session_id": session_id or os.environ.get("OPENCLAW_SESSION_ID", ""),
        "task_type": task_type,
        "model": model or os.environ.get("OPENCLAW_MODEL", ""),
        "success": success,
        "quality": max(1, min(5, quality)),
        "duration_ms": duration_ms,
        "issues": [i for i in (issues or []) if i in ISSUE_TYPES],
        "tags": tags or [],
        "notes": notes,
    }

    with open(OUTCOMES_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

    return record

def stats_summary(days: int = 7):
    """Return summary stats from recent outcomes."""
    outcomes = load_outcomes()
    if not outcomes:
        return {"total": 0, "message": "No outcomes logged yet"}

    cutoff = time.time() - (days * 86400)
    recent = []
    for o in outcomes:
        try:
            ts = datetime.fromisoformat(o["ts"]).timestamp()
            if ts >= cutoff:
                recent.append(o)
        except Exception:
            pass

    if not recent:
        return {"total": 0, "message": f"No outcomes in last {days} days"}

    total = len(recent)
    success = sum(1 for o in recent if o.get("success"))
    avg_quality = sum(o.get("quality", 3) for o in recent) / total

    issue_counts = {}
    for o in recent:
        for issue in o.get("issues", []):
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

    task_counts = {}
    for o in recent:
        tt = o.get("task_type", "unknown")
        task_counts[tt] = task_counts.get(tt, 0) + 1

    return {
        "period_days": days,
        "total": total,
        "success_rate": round(success / total, 3),
        "avg_quality": round(avg_quality, 2),
        "top_issues": sorted(issue_counts.items(), key=lambda x: -x[1])[:5],
        "top_tasks": sorted(task_counts.items(), key=lambda x: -x[1])[:5],
    }

def main():
    parser = argparse.ArgumentParser(description="RSI Observer - Log agent turn outcomes")
    sub = parser.add_subparsers(dest="cmd")

    # log command
    log_cmd = sub.add_parser("log", help="Log a turn outcome")
    log_cmd.add_argument("--task", required=True, choices=TASK_TYPES, help="Task type")
    log_cmd.add_argument("--success", required=True, choices=["true", "false"])
    log_cmd.add_argument("--quality", type=int, default=3, help="Quality 1-5")
    log_cmd.add_argument("--model", default="")
    log_cmd.add_argument("--duration-ms", type=int, default=0)
    log_cmd.add_argument("--issues", nargs="*", default=[], choices=ISSUE_TYPES)
    log_cmd.add_argument("--tags", nargs="*", default=[])
    log_cmd.add_argument("--notes", default="")
    log_cmd.add_argument("--agent-id", default="main")
    log_cmd.add_argument("--session-id", default="")

    # stats command
    stats_cmd = sub.add_parser("stats", help="Show outcome stats")
    stats_cmd.add_argument("--days", type=int, default=7)

    # types command
    sub.add_parser("types", help="List valid task/issue types")

    args = parser.parse_args()

    if args.cmd == "log":
        record = log_outcome(
            task_type=args.task,
            success=args.success == "true",
            quality=args.quality,
            model=args.model,
            duration_ms=args.duration_ms,
            issues=args.issues,
            tags=args.tags,
            notes=args.notes,
            agent_id=args.agent_id,
            session_id=args.session_id,
        )
        print(f"Logged: {record['id']} | {record['task_type']} | success={record['success']} | quality={record['quality']}")

    elif args.cmd == "stats":
        stats = stats_summary(args.days)
        print(json.dumps(stats, indent=2))

    elif args.cmd == "types":
        print("Task types:", TASK_TYPES)
        print("Issue types:", ISSUE_TYPES)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
