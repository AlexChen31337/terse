#!/bin/bash
# Daily Claude Code CLI updater
# Runs `claude update`, logs result, restarts shim if version changed

set -u

LOG=/home/bowen/.openclaw/workspace/memory/claude-code-update.log
SHIM_PID_PATTERN="claude_code_shim.py"
CLAUDE_BIN=/home/bowen/.local/bin/claude

mkdir -p "$(dirname "$LOG")"

log() {
  echo "[$(date -Iseconds)] $*" >> "$LOG"
}

# Current version
OLD_VERSION=$("$CLAUDE_BIN" --version 2>/dev/null | awk '{print $1}')
log "check start: current version=$OLD_VERSION"

# Run update
UPDATE_OUTPUT=$("$CLAUDE_BIN" update 2>&1)
UPDATE_RC=$?
log "update output: $UPDATE_OUTPUT"
log "update rc: $UPDATE_RC"

# New version
NEW_VERSION=$("$CLAUDE_BIN" --version 2>/dev/null | awk '{print $1}')
log "new version: $NEW_VERSION"

if [ "$OLD_VERSION" != "$NEW_VERSION" ]; then
  log "version changed: $OLD_VERSION -> $NEW_VERSION, restarting shim"
  # Kill existing shim python + supervisor
  pkill -f "$SHIM_PID_PATTERN" 2>/dev/null
  pkill -f "claude_code_shim_supervisor" 2>/dev/null
  sleep 2
  # Restart via supervisor (won't persist beyond this script, must use nohup+setsid)
  setsid nohup bash /home/bowen/.openclaw/workspace/scripts/claude_code_shim_supervisor.sh </dev/null >/dev/null 2>&1 &
  disown
  sleep 3
  # Health check
  HEALTH=$(curl -sS -m 5 http://127.0.0.1:8090/health 2>&1)
  log "shim health after restart: $HEALTH"
  echo "VERSION_CHANGED:$OLD_VERSION->$NEW_VERSION"
else
  log "no version change"
  echo "NO_CHANGE:$OLD_VERSION"
fi

# Trim log if > 5MB
if [ -f "$LOG" ] && [ "$(stat -c%s "$LOG")" -gt 5242880 ]; then
  tail -500 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"
fi
