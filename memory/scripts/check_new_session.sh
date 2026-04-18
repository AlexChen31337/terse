#!/bin/bash
# Detect if the main OpenClaw session has been reset since last tracked.
# Outputs: CURRENT_ID|STORED_ID
# Exit 0 = same session, Exit 1 = new session detected

STATE_FILE="/home/bowen/clawd/memory/heartbeat-state.json"
SESSIONS_DIR="/home/bowen/.openclaw/agents/main/sessions"

# Find most recent active session (exclude .reset. and .deleted. files)
CURRENT_FILE=$(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null | grep -v "\.reset\.\|\.deleted\." | head -1)
CURRENT_ID=$(basename "$CURRENT_FILE" .jsonl 2>/dev/null)

if [ -z "$CURRENT_ID" ]; then
    echo "ERROR: No active session found"
    exit 2
fi

# Get stored session ID
STORED_ID=""
if [ -f "$STATE_FILE" ]; then
    STORED_ID=$(python3 -c "
import json, sys
try:
    with open('$STATE_FILE') as f:
        d = json.load(f)
    print(d.get('lastSessionId', ''))
except Exception:
    print('')
" 2>/dev/null)
fi

echo "${CURRENT_ID}|${STORED_ID}"

if [ "$CURRENT_ID" != "$STORED_ID" ]; then
    exit 1  # New session
else
    exit 0  # Same session
fi
