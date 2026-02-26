#!/usr/bin/env python3
"""
session-guard: Active session size enforcer.
Monitors the main session file size and triggers a gateway restart when
it exceeds thresholds. Three-tier protection:

  WARN zone (warn-mb → crit-mb): Alert user, no restart yet.
  CRIT zone (crit-mb → hard-mb): Restart if idle >= crit-idle-minutes (default 1).
  HARD ceiling (hard-mb+):       Always restart, no idle check. No mercy.

Usage:
  python3 size_watcher.py
  python3 size_watcher.py --warn-mb 6 --crit-mb 8 --hard-mb 10
  python3 size_watcher.py --dry-run

Output codes (first token on stdout):
  OK            - under warn threshold, all good
  WARN          - in warn zone, user should be alerted
  SKIPPED_ACTIVE- in crit zone but session still active (idle < crit-idle-minutes)
  RESTARTED     - restart triggered (crit+idle or hard ceiling)
  RESTART_FAILED- restart attempted but failed
  ERROR         - unexpected problem
"""
import os
import sys
import glob
import argparse
import subprocess
import time
from datetime import datetime
from pathlib import Path

DEFAULT_SESSIONS_DIR = os.path.expanduser("~/.openclaw/agents/main/sessions")
DEFAULT_LOG = os.path.expanduser("~/clawd/memory/session-guard.log")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--warn-mb",          type=float, default=6.0,
                   help="Alert zone start (default: 6MB)")
    p.add_argument("--crit-mb",          type=float, default=8.0,
                   help="Restart-if-idle threshold (default: 8MB)")
    p.add_argument("--hard-mb",          type=float, default=10.0,
                   help="Hard ceiling — always restart, no idle check (default: 10MB)")
    p.add_argument("--idle-minutes",     type=float, default=5.0,
                   help="Idle required for WARN restart (legacy, ignored now)")
    p.add_argument("--crit-idle-minutes",type=float, default=1.0,
                   help="Idle required for CRIT restart (default: 1 min)")
    p.add_argument("--sessions-dir",     default=DEFAULT_SESSIONS_DIR)
    p.add_argument("--log-file",         default=DEFAULT_LOG)
    p.add_argument("--dry-run",          action="store_true")
    return p.parse_args()


def find_active_session(sessions_dir):
    """Return (path, size_mb, idle_minutes) for the most recent active session."""
    pattern = os.path.join(sessions_dir, "*.jsonl")
    files = glob.glob(pattern)
    active = [f for f in files if ".reset." not in f and ".deleted." not in f]
    if not active:
        return None, 0, 0
    active.sort(key=os.path.getmtime, reverse=True)
    path = active[0]
    size_mb = os.path.getsize(path) / (1024 * 1024)
    idle_seconds = time.time() - os.path.getmtime(path)
    return path, size_mb, idle_seconds / 60


def trigger_restart(dry_run=False):
    """Trigger openclaw gateway restart. Returns (success, message)."""
    if dry_run:
        return True, "DRY_RUN: would run 'openclaw gateway restart'"
    try:
        result = subprocess.run(
            ["openclaw", "gateway", "restart"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return True, result.stdout.strip() or "Gateway restart initiated"
        return False, f"exit {result.returncode}: {result.stderr.strip()[:200]}"
    except FileNotFoundError:
        return False, "openclaw CLI not found"
    except subprocess.TimeoutExpired:
        return False, "restart command timed out"
    except Exception as e:
        return False, str(e)


def log_line(log_file, level, message):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {message}"
    print(line)
    try:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def main():
    args = parse_args()
    path, size_mb, idle_min = find_active_session(args.sessions_dir)

    if path is None:
        print(f"ERROR no active session in {args.sessions_dir}")
        sys.exit(1)

    sid = os.path.basename(path)[:36]
    s = f"{size_mb:.1f}MB"

    # ── Zone 1: OK ─────────────────────────────────────────────────────────
    if size_mb < args.warn_mb:
        print(f"OK {s} (warn: {args.warn_mb}MB) — {sid}")
        sys.exit(0)

    # ── Zone 2: WARN — alert but don't restart yet ─────────────────────────
    if size_mb < args.crit_mb:
        msg = (f"WARN {s} — session approaching limit "
               f"(warn:{args.warn_mb}MB crit:{args.crit_mb}MB hard:{args.hard_mb}MB) — {sid}")
        log_line(args.log_file, "WARN", msg)
        print(msg)
        sys.exit(0)

    # ── Zone 3: HARD ceiling — always restart, no questions asked ──────────
    if size_mb >= args.hard_mb:
        pre = (f"HARD CEILING {s} >= {args.hard_mb}MB — "
               f"forcing restart (idle {idle_min:.1f}min, no check) — {sid}")
        log_line(args.log_file, "CRIT", pre)
        success, rmsg = trigger_restart(dry_run=args.dry_run)
        if success:
            out = f"RESTARTED {s} (hard-ceiling) — {rmsg}"
            log_line(args.log_file, "INFO", out)
            print(out)
            sys.exit(0)
        else:
            out = f"RESTART_FAILED {s} (hard-ceiling) — {rmsg}"
            log_line(args.log_file, "ERROR", out)
            print(out)
            sys.exit(2)

    # ── Zone 4: CRIT — restart only if idle long enough ────────────────────
    if idle_min < args.crit_idle_minutes:
        msg = (f"SKIPPED_ACTIVE {s} — idle {idle_min:.1f}min "
               f"(need {args.crit_idle_minutes}min for crit restart) — {sid}")
        log_line(args.log_file, "WARN", msg)
        print(msg)
        sys.exit(0)

    pre = (f"CRITICAL {s} (>{args.crit_mb}MB), idle {idle_min:.1f}min — "
           f"triggering restart — {sid}")
    log_line(args.log_file, "CRIT", pre)
    success, rmsg = trigger_restart(dry_run=args.dry_run)
    if success:
        out = f"RESTARTED {s} (crit+idle) — {rmsg}"
        log_line(args.log_file, "INFO", out)
        print(out)
        sys.exit(0)
    else:
        out = f"RESTART_FAILED {s} (crit+idle) — {rmsg}"
        log_line(args.log_file, "ERROR", out)
        print(out)
        sys.exit(2)


if __name__ == "__main__":
    main()
