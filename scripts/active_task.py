#!/usr/bin/env python3
"""
Active Task WAL (Write-Ahead Log) — Session Continuity Protocol

Tracks what task was in-flight when compaction/restart hits.
On next session start, AGENTS.md checks this file and resumes.

Usage:
    # Start a task
    uv run python scripts/active_task.py start "EvoClaw coverage boost" \
        --step "Writing test_agent_api.go (3/5)" \
        --context "Builder spawned, 3 test files done"

    # Update step mid-task
    uv run python scripts/active_task.py update --step "Running tests (4/5)"

    # Mark done (clears the file)
    uv run python scripts/active_task.py done

    # Check if a task is in-flight
    uv run python scripts/active_task.py status

    # Print resume prompt (for AGENTS.md session start)
    uv run python scripts/active_task.py resume
"""

import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
ACTIVE_TASK_FILE = WORKSPACE / "memory" / "active-task.json"
ARCHIVE_FILE = WORKSPACE / "memory" / "active-task-history.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load() -> dict | None:
    if not ACTIVE_TASK_FILE.exists():
        return None
    try:
        return json.loads(ACTIVE_TASK_FILE.read_text())
    except Exception:
        return None


def save(data: dict):
    ACTIVE_TASK_FILE.parent.mkdir(exist_ok=True)
    ACTIVE_TASK_FILE.write_text(json.dumps(data, indent=2))


def archive(data: dict, outcome: str):
    """Append completed/interrupted task to history."""
    ARCHIVE_FILE.parent.mkdir(exist_ok=True)
    entry = {**data, "ended_at": now_iso(), "outcome": outcome}
    with open(ARCHIVE_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def cmd_start(args):
    existing = load()
    if existing:
        # Archive the interrupted task before starting new one
        archive(existing, "interrupted")
        print(f"⚠️  Previous task archived as interrupted: {existing['task'][:60]}")

    data = {
        "task": args.task,
        "step": args.step or "Starting",
        "started_at": now_iso(),
        "updated_at": now_iso(),
        "context": args.context or "",
        "tags": args.tags or [],
    }
    save(data)
    print(f"✅ Active task set: {args.task}")
    if args.step:
        print(f"   Step: {args.step}")


def cmd_update(args):
    data = load()
    if not data:
        print("No active task. Use 'start' first.", file=sys.stderr)
        sys.exit(1)

    if args.step:
        data["step"] = args.step
    if args.context:
        data["context"] = args.context
    data["updated_at"] = now_iso()
    save(data)
    print(f"✅ Updated: {data['step']}")


def cmd_done(args):
    data = load()
    if not data:
        print("No active task to complete.")
        return

    archive(data, "completed")
    ACTIVE_TASK_FILE.unlink()
    print(f"✅ Task completed and archived: {data['task'][:60]}")


def cmd_status(args):
    data = load()
    if not data:
        print("No active task.")
        return 0

    started = data.get("started_at", "unknown")
    updated = data.get("updated_at", started)
    print(f"🔄 ACTIVE TASK IN FLIGHT")
    print(f"   Task:    {data['task']}")
    print(f"   Step:    {data['step']}")
    print(f"   Started: {started}")
    print(f"   Updated: {updated}")
    if data.get("context"):
        print(f"   Context: {data['context']}")
    return 1  # exit 1 = task exists (useful in shell conditionals)


def cmd_resume(args):
    """Print a human-readable resume prompt for session start."""
    data = load()
    if not data:
        # No task in flight — session start is clean
        sys.exit(0)

    # Calculate how long ago
    try:
        started = datetime.fromisoformat(data["started_at"])
        updated = datetime.fromisoformat(data["updated_at"])
        now = datetime.now(timezone.utc)
        elapsed_h = (now - updated).total_seconds() / 3600
        elapsed_str = f"{elapsed_h:.1f}h ago"
    except Exception:
        elapsed_str = "unknown time ago"

    print(
        f"⚠️  TASK WAS IN FLIGHT — RESUME REQUIRED\n"
        f"Task:    {data['task']}\n"
        f"Step:    {data['step']}\n"
        f"Updated: {elapsed_str}\n"
        f"Context: {data.get('context', 'none')}\n"
        f"\n"
        f"Before doing anything else: resume this task or explicitly mark it done.\n"
        f"  Mark done:   uv run python scripts/active_task.py done\n"
        f"  Update step: uv run python scripts/active_task.py update --step 'new step'"
    )
    sys.exit(1)  # exit 1 = task exists, AGENTS.md uses this


def cmd_history(args):
    if not ARCHIVE_FILE.exists():
        print("No task history yet.")
        return

    lines = ARCHIVE_FILE.read_text().strip().splitlines()
    limit = args.limit or 5
    recent = lines[-limit:]
    print(f"Last {len(recent)} tasks:")
    for line in recent:
        try:
            e = json.loads(line)
            icon = "✅" if e.get("outcome") == "completed" else "⚡"
            print(f"  {icon} [{e.get('outcome','?'):12s}] {e['task'][:55]} | {e.get('step','?')[:30]}")
        except Exception:
            print(f"  ? {line[:80]}")


def main():
    parser = argparse.ArgumentParser(description="Active Task WAL — session continuity")
    sub = parser.add_subparsers(dest="cmd")

    # start
    p_start = sub.add_parser("start", help="Start tracking a task")
    p_start.add_argument("task", help="Task description")
    p_start.add_argument("--step", help="Current step description")
    p_start.add_argument("--context", help="Extra context (file paths, state, etc.)")
    p_start.add_argument("--tags", nargs="*", help="Tags")

    # update
    p_update = sub.add_parser("update", help="Update current step")
    p_update.add_argument("--step", help="New step description")
    p_update.add_argument("--context", help="Updated context")

    # done
    sub.add_parser("done", help="Mark task complete and clear")

    # status
    sub.add_parser("status", help="Show current active task")

    # resume
    sub.add_parser("resume", help="Print resume prompt (for session start)")

    # history
    p_hist = sub.add_parser("history", help="Show recent task history")
    p_hist.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()

    cmds = {
        "start": cmd_start,
        "update": cmd_update,
        "done": cmd_done,
        "status": cmd_status,
        "resume": cmd_resume,
        "history": cmd_history,
    }

    if not args.cmd:
        parser.print_help()
        sys.exit(2)

    fn = cmds.get(args.cmd)
    if fn:
        result = fn(args)
        if isinstance(result, int):
            sys.exit(result)
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
