---
metadata.openclaw:
  always: true
  reason: "Auto-classified as always-load (no specific rule for 'session-guard')"
---


# Session Guard

Fixes the OpenClaw heartbeat-in-main-session architectural gap that causes session files to bloat, corrupt, and reset — losing all agent context.

## The Problem

OpenClaw's built-in `heartbeat` runs exclusively in the main session. Every heartbeat turn accumulates as conversation history, inflating the session `.jsonl` file indefinitely. With hourly heartbeats over 2+ days, this reaches 10–15MB, corrupting the file header and triggering an automatic session reset — silently wiping all context.

**Secondary bug**: When heartbeat returns `HEARTBEAT_OK`, OpenClaw strips it but still tries to forward an empty string to messaging platforms → `sendMessage error: message text is empty` spam. Unfixable from agent side.

## One-Shot Install (recommended)

Applies all protections automatically in a single command:

```bash
python3 skills/session-guard/scripts/install.py
```

This runs all 5 steps:
1. **Config patch** — disables built-in heartbeat (`every: 0m`), sets `compaction: default`
2. **Isolated heartbeat cron** — 1h interval, reads HEARTBEAT.md in isolated session
3. **Session wake monitor cron** — 5min interval, detects resets and triggers hydration
4. **Session size watcher cron** — 15min interval, restarts gateway if session exceeds 8MB + idle
5. **Init session ID** — stores current session ID for wake detection baseline

Options:
```bash
python3 install.py --dry-run                        # preview all changes, no writes
python3 install.py --heartbeat-model anthropic-proxy-4/glm-4.7  # model for heartbeat cron
python3 install.py --monitor-model nvidia-nim/qwen/qwen2.5-7b-instruct  # model for monitors
python3 install.py --crit-mb 8 --hard-mb 10 --warn-mb 6  # custom thresholds
python3 install.py --skip-crons                     # config patch only
python3 install.py --workspace /custom/path
```

Auto-detects gateway URL and token from `~/.openclaw/openclaw.json`. Skips any crons that already exist (idempotent).

---

## Quick Audit

Run to detect issues:

```bash
python3 skills/session-guard/scripts/audit.py
```

Output: lists config antipatterns (heartbeat enabled, safeguard compaction) and session file sizes.

## Fix: Disable Built-in Heartbeat

If audit finds `heartbeat.every` is set (non-zero), patch the config:

```python
# Via gateway tool:
gateway(action="config.patch", raw=json.dumps({
    "agents": {
        "defaults": {
            "heartbeat": {"every": "0m"},
            "compaction": {"mode": "default"}
        }
    }
}), note="Disabled main-session heartbeat to prevent bloat")
```

## Fix: Create Isolated Heartbeat Cron

Replace the disabled built-in heartbeat with an isolated cron job. Use a cheap model. The isolated session reads HEARTBEAT.md and sends Telegram alerts directly via `message` tool (isolated sessions don't auto-deliver to channels).

```python
cron(action="add", job={
    "name": "Isolated Heartbeat",
    "schedule": {"kind": "every", "everyMs": 3600000},  # 1h
    "payload": {
        "kind": "agentTurn",
        "model": "anthropic-proxy-4/glm-4.7",  # cheap model
        "message": "Read HEARTBEAT.md and follow it. Send Telegram alerts via message tool for anything urgent. Do NOT reply HEARTBEAT_OK — isolated sessions must use message tool to notify.",
        "timeoutSeconds": 120
    },
    "sessionTarget": "isolated"
})
```

## Fix: Session Wake Detection

To detect when OpenClaw resets the session and re-inject context automatically:

**Step 1**: Set up the wake monitor cron (runs every 5 min on cheapest model):

```python
cron(action="add", job={
    "name": "Session Wake Monitor",
    "schedule": {"kind": "every", "everyMs": 300000},  # 5min
    "payload": {
        "kind": "agentTurn",
        "model": "nvidia-nim/qwen/qwen2.5-7b-instruct",
        "message": """Check if main session has reset:
1. Run: bash skills/session-guard/scripts/check_session.sh
   Output: CURRENT_ID|STORED_ID. Exit 0=same, 1=new, 2=error.
2. If exit 1 (new session):
   a. Update ID: python3 skills/session-guard/scripts/update_session_id.py <CURRENT_ID>
   b. Notify main session via sessions_send to trigger hydration.
3. If exit 0: do nothing, reply DONE.""",
        "timeoutSeconds": 60
    },
    "sessionTarget": "isolated"
})
```

**Step 2**: Add session wake detection to HEARTBEAT.md so every heartbeat also checks:

```markdown
## Session Wake Detection (run first on every heartbeat)
1. bash memory/scripts/check_new_session.sh
2. If exit 1: hydrate context (read today's daily notes, search tiered memory), update ID
```

**Step 3**: Initialize stored session ID (first time only):

```bash
# Get current session ID
ls -t ~/.openclaw/agents/main/sessions/*.jsonl | grep -v '\.reset\.' | head -1 | xargs basename | sed 's/\.jsonl//'
# Then store it:
python3 skills/session-guard/scripts/update_session_id.py <ID>
```

## Monitoring Session Size

Check if current sessions are bloating:

```bash
python3 skills/session-guard/scripts/audit.py --warn-mb 3
```

Thresholds: warn at 6MB, crit at 8MB, hard ceiling at 10MB. A healthy active session stays under 2MB with `compaction: "default"`.

## Hydration: Re-inject Context After Session Reset

When a session reset is detected, run hydration to rebuild context:

```bash
python3 skills/session-guard/scripts/hydrate.py
```

This loads and concatenates:
1. **Daily notes** — last 2 days from `memory/YYYY-MM-DD.md`
2. **Tiered memory** — top-3 relevant nodes via tree search
3. **MEMORY.md** — first 2000 chars of long-term memory

Output is a structured markdown summary. Read it, synthesize the key context, then notify the user that the session was reset and you've reloaded context.

**Options:**
```bash
python3 hydrate.py --days 3              # load 3 days of notes (default: 2)
python3 hydrate.py --memory-limit 5     # fetch 5 tiered memory results (default: 3)
python3 hydrate.py --workspace /path    # explicit workspace (default: auto-detect ~/clawd)
```

**Full wake detection + hydration flow (used in Session Wake Monitor cron):**

```
1. bash skills/session-guard/scripts/check_session.sh
   → exit 0: same session, skip
   → exit 1: NEW SESSION — proceed with hydration

2. python3 skills/session-guard/scripts/hydrate.py > /tmp/hydration.txt
   cat /tmp/hydration.txt  # read and synthesize

3. python3 skills/session-guard/scripts/update_session_id.py <CURRENT_ID>

4. Notify user (via message tool in isolated sessions):
   "🔄 Session reset detected — context reloaded. [brief summary of key projects/state]"
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/audit.py` | Audit config + session sizes. Args: `--config`, `--sessions-dir`, `--warn-mb`, `--json` |
| `scripts/check_session.sh` | Detect session ID change. Exit 0=same, 1=new, 2=error. Args: [state_file] [sessions_dir] |
| `scripts/update_session_id.py` | Store new session ID. Args: `<id>` [state_file] |
| `scripts/hydrate.py` | Load recent daily notes + tiered memory + MEMORY.md into a summary. Args: `--days`, `--memory-limit`, `--workspace` |
| `scripts/size_watcher.py` | Three-tier session size enforcer. Args: `--warn-mb` (6), `--crit-mb` (8), `--hard-mb` (10), `--crit-idle-minutes` (1), `--dry-run` |
| `scripts/install.py` | **One-shot installer** — applies all 5 protections automatically. Args: `--dry-run`, `--skip-crons`, `--crit-mb`, `--heartbeat-model`, `--monitor-model`, `--workspace` |

State file default: `~/clawd/memory/heartbeat-state.json` (key: `lastSessionId`).
Override via `GUARD_STATE_FILE` env var or script argument.

## Active Size Enforcement (size_watcher.py)

Proactively restarts the gateway before the session corrupts. Uses a **three-tier** protection model:

| Zone | Range | Action |
|------|-------|--------|
| OK | < 6MB | Silent |
| WARN | 6–8MB | Alert user via Telegram, no restart |
| CRIT | 8–10MB | Restart if idle ≥ 1 min |
| HARD | ≥ 10MB | **Always** restart — no idle check |

```bash
uv run python skills/session-guard/scripts/size_watcher.py
uv run python skills/session-guard/scripts/size_watcher.py --warn-mb 6 --crit-mb 8 --hard-mb 10 --crit-idle-minutes 1
uv run python skills/session-guard/scripts/size_watcher.py --dry-run  # check only
```

**How it works:**
1. Finds the most-recently-modified active session file (= current main session)
2. If size < `--warn-mb` (default 6MB): exits `OK`
3. If 6MB ≤ size < 8MB (`--crit-mb`): logs `WARN`, sends Telegram alert — user should `/new` soon
4. If 8MB ≤ size < 10MB (`--hard-mb`) AND idle ≥ `--crit-idle-minutes` (default 1min): restarts gateway
5. If size ≥ `--hard-mb` (10MB): **always** restarts regardless of idle — prevents overflow in active sessions
6. After restart: Session Wake Monitor detects new session → runs `hydrate.py` → notifies user

**Why the hard ceiling matters**: The CRIT idle check exists to avoid mid-conversation interruption. But an actively-used session can grow past 10MB before the check fires. The hard ceiling ensures the session never hits a model context overflow regardless of activity.

**Add as a cron job (every 15 min, cheap model):**

```python
cron(action="add", job={
    "name": "Session Size Watcher",
    "schedule": {"kind": "every", "everyMs": 900000},
    "payload": {
        "kind": "agentTurn",
        "model": "anthropic-proxy-4/glm-4.7",
        "message": """Run: uv run python skills/session-guard/scripts/size_watcher.py --warn-mb 6 --crit-mb 8 --hard-mb 10 --crit-idle-minutes 1

Handle output based on FIRST word:
- 'OK': reply DONE
- 'WARN': send Telegram to target=2069029798: '⚠️ Session growing large. Consider /new soon to avoid overflow.' Reply DONE.
- 'SKIPPED_ACTIVE': reply DONE (will retry next cycle)
- 'RESTARTED': send Telegram to target=2069029798: '🔄 Session size limit hit — gateway restarted to prevent context overflow.' Reply DONE.
- 'RESTART_FAILED': send Telegram to target=2069029798: '⚠️ Session bloat critical but restart failed. Please run /reset manually.' Reply DONE.
- 'ERROR': reply DONE""",
        "timeoutSeconds": 60
    },
    "sessionTarget": "isolated"
})
```

Logs to `~/clawd/memory/session-guard.log` for audit trail.

## Known OpenClaw Bugs (cannot fix from agent side)

1. `heartbeat.session` config only supports `"main"` — no isolated option
2. `HEARTBEAT_OK` stripped → empty string forwarded to messaging → sendMessage error
3. `compaction.mode: "safeguard"` default too conservative for long-running agents
