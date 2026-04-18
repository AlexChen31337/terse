# agent-watchdog — PLAN.md

## 1. Architecture & Data Flow

```
~/.openclaw/agents/*/sessions/*.jsonl  (input — session files)
        │
        ▼
   watchdog.py  ←── config.json (thresholds)
        │
        ├─ Detector 1: spawn_explosion — parses recent tool calls
        ├─ Detector 2: stagnation — checks file growth over time
        └─ Detector 3: long_runner — checks session age vs category
        │
        ▼
   Kill decision (or dry-run log)
        │
        ├─ POST localhost:18789/api/sessions/{key}/terminate
        ├─ Append to data/kills.jsonl
        └─ Print alert to stdout
```

**Flow:**
1. Glob `~/.openclaw/agents/*/sessions/*.jsonl`
2. Filter to files with mtime within `active_window_min` (default 30) minutes
3. For each file, extract session key from path: `agent:{agent_name}:{stem}`
4. Skip sessions matching `skip_patterns` (default: `["agent:main:main"]`)
5. Run detectors in order; first KILL verdict wins
6. Execute kill or log dry-run

## 2. File Structure

```
~/clawd/skills/agent-watchdog/
├── PLAN.md          # this file
├── SKILL.md         # skill descriptor
├── config.json      # all tuneable thresholds
├── watchdog.py      # single-file implementation (<300 lines)
└── data/
    └── kills.jsonl  # kill log (created on first kill)
```

### watchdog.py — Functions

```python
import json, glob, os, sys, time, argparse, datetime, re
from pathlib import Path
from typing import Optional

# --- Config ---
def load_config(config_path: Path) -> dict:
    """Load config.json, return defaults if missing."""

# --- Session Discovery ---
def discover_sessions(agents_dir: Path, active_window_min: int) -> list[dict]:
    """
    Glob *.jsonl under agents_dir/*/sessions/.
    Return list of:
      {"path": Path, "session_key": str, "mtime": float, "agent": str, "stem": str}
    Filter to mtime within active_window_min of now.
    """

# --- File Parsing ---
def tail_lines(path: Path, max_lines: int = 200) -> list[str]:
    """Read last max_lines of a file. Graceful on read errors."""

def parse_jsonl_lines(lines: list[str]) -> list[dict]:
    """Parse JSONL lines into dicts, skip malformed."""

def count_lines(path: Path) -> int:
    """Count total lines in file. Returns 0 on error."""

# --- Detectors ---
def detect_spawn_explosion(entries: list[dict], cfg: dict) -> Optional[str]:
    """
    Look for tool_use entries where name == 'sessions_spawn'.
    Extract timestamps from entries.
    If >cfg['spawn_explosion']['max_spawns'] within cfg['spawn_explosion']['window_sec'] seconds → return reason string.
    Returns None if clean.
    """

def detect_stagnation(path: Path, line_count: int, session_age_sec: float, cfg: dict) -> Optional[str]:
    """
    Read cfg['stagnation']['check_file'] — a state file at data/stagnation_state.json.
    Compare current line_count to previously recorded count for this path.
    If delta <= cfg['stagnation']['min_growth_lines'] (default 5)
       AND elapsed since last check >= cfg['stagnation']['check_interval_sec'] (default 300)
       AND session_age_sec > cfg['stagnation']['min_age_sec'] (default 600)
    → return reason string.
    Always update state file with current counts.
    Returns None if clean or first check.
    """

def detect_long_runner(session_key: str, session_age_sec: float, cfg: dict) -> Optional[str]:
    """
    Classify session by label keywords in session_key:
      - matches any in cfg['long_runner']['monitoring_keywords'] → monitoring threshold
      - matches any in cfg['long_runner']['medium_keywords'] → medium threshold
      - else → default threshold
    Skip if session_key matches any skip_patterns.
    If session_age_sec > threshold → return reason string.
    Returns None if clean.
    """

# --- Kill Action ---
def kill_session(session_key: str, gateway_url: str, gateway_token: str, dry_run: bool) -> bool:
    """
    POST {gateway_url}/api/sessions/{session_key}/terminate
    Headers: Authorization: Bearer {gateway_token}
    Returns True if killed (or dry_run). False on error.
    """

def log_kill(kill_entry: dict, kills_path: Path) -> None:
    """Append JSON line to kills.jsonl. Create parent dirs if needed."""

# --- Main ---
def main() -> None:
    """
    argparse:
      --config PATH   (default: script_dir/config.json)
      --dry-run       (log but don't kill)
      --verbose       (print all sessions checked)
    
    Reads OPENCLAW_GATEWAY_TOKEN from env (required unless --dry-run).
    Gateway URL from config (default http://localhost:18789).
    
    For each active session:
      1. tail + parse entries
      2. Run detectors
      3. If verdict: kill (or dry-run), log, print alert
    
    Exit code: 0 if no kills, 1 if any kills executed.
    """
```

## 3. CLI Interface

```bash
# Normal run (kills runaway sessions)
OPENCLAW_GATEWAY_TOKEN=xxx uv run python watchdog.py

# Dry run (detect only, no kills)
uv run python watchdog.py --dry-run

# Custom config
uv run python watchdog.py --config /path/to/config.json

# Verbose (show all sessions scanned)
uv run python watchdog.py --dry-run --verbose
```

**Exit codes:** 0 = clean, 1 = kills executed (or would-be in dry-run)

## 4. Config Schema — config.json

```json
{
  "gateway_url": "http://localhost:18789",
  "agents_dir": "~/.openclaw/agents",
  "active_window_min": 30,
  "skip_patterns": ["agent:main:main"],

  "spawn_explosion": {
    "enabled": true,
    "max_spawns": 3,
    "window_sec": 120
  },

  "stagnation": {
    "enabled": true,
    "min_growth_lines": 5,
    "check_interval_sec": 300,
    "min_age_sec": 600,
    "state_file": "data/stagnation_state.json"
  },

  "long_runner": {
    "enabled": true,
    "monitoring_keywords": ["heartbeat", "monitor", "check", "health", "watchdog"],
    "medium_keywords": ["build", "review", "plan", "fix", "patch"],
    "thresholds_sec": {
      "monitoring": 480,
      "medium": 1200,
      "default": 1800
    }
  }
}
```

## 5. Data Models

### Session info (internal)
```python
@dataclass  # or just dict
SessionInfo:
    path: Path
    session_key: str      # "agent:{agent}:{stem}"
    agent: str            # agent dir name
    stem: str             # filename without .jsonl
    mtime: float          # unix timestamp
    age_sec: float        # now - mtime of first entry or file ctime
    line_count: int
```

### Kill log entry (kills.jsonl)
```json
{
  "ts": "2026-02-25T08:00:00+11:00",
  "session_key": "agent:main:subagent:abc123",
  "detector": "spawn_explosion",
  "reason": "5 spawns in 90s (threshold: 3 in 120s)",
  "dry_run": false,
  "killed": true
}
```

### Stagnation state (data/stagnation_state.json)
```json
{
  "/home/user/.openclaw/agents/main/sessions/sub-abc.jsonl": {
    "line_count": 450,
    "checked_at": 1740441600.0
  }
}
```

## 6. Error Handling Strategy

| Scenario | Handling |
|---|---|
| agents_dir missing | Log warning, exit 0 (nothing to check) |
| Session file unreadable | Skip, log warning if --verbose |
| Malformed JSONL line | Skip line, continue parsing |
| config.json missing | Use all defaults (hardcoded) |
| Gateway token missing | Error + exit 1 (unless --dry-run) |
| Kill API returns non-200 | Log error, continue to next session |
| stagnation_state.json corrupt | Delete and restart fresh |
| requests import fails | Print install hint, exit 1 |
| Permission errors on kills.jsonl | Print warning, continue |

**Principle:** Never crash. Log and continue. One bad session file must not block checking others.

## 7. Test Plan

### Unit tests (manual verification, no test framework needed)

1. **discover_sessions** — create temp dir with mock .jsonl files (some old, some recent), verify filtering
2. **detect_spawn_explosion** — feed entries with N spawn calls at known timestamps, verify threshold triggers
3. **detect_stagnation** — run twice with same line count, verify second run triggers
4. **detect_long_runner** — test keyword matching and threshold logic for each category
5. **skip_patterns** — verify main session is never killed
6. **parse_jsonl_lines** — mix of valid/invalid JSON, verify graceful skip

### Integration test

```bash
# 1. Create mock session files
mkdir -p /tmp/test-agents/main/sessions
# write mock .jsonl with spawn explosions
# 2. Run dry-run against mock dir
uv run python watchdog.py --dry-run --config /tmp/test-config.json --verbose
# 3. Verify stdout shows detection + dry-run kill
# 4. Verify kills.jsonl has entry with dry_run=true
```

### Edge cases to verify
- Empty session file → skip gracefully
- Session file with only 1 line → no stagnation trigger (too young)
- Main session → never killed regardless of detectors
- All detectors disabled in config → no kills
- No gateway token + no --dry-run → error exit

---

**Builder:** Implement `watchdog.py`, `config.json`, `SKILL.md` exactly as specified above. Target <300 lines for watchdog.py.
