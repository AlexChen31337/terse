#!/usr/bin/env bash
# Sync Claude Code's refreshed OAuth token back into OpenClaw config
# Run this when openclaw's anthropic/ provider starts failing with 401
set -euo pipefail

CREDS_FILE="$HOME/.claude/.credentials.json"
STATE_FILE="$HOME/.openclaw/workspace/memory/oauth-health.json"
LOG="$HOME/.openclaw/workspace/memory/oauth-sync.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

if [[ ! -f "$CREDS_FILE" ]]; then
  log "ERROR: Claude Code credentials not found at $CREDS_FILE"
  exit 1
fi

# Extract fresh token and expiry from Claude Code's credential store
FRESH_TOKEN=$(python3 -c "
import json
d = json.load(open('$CREDS_FILE'))
oauth = d.get('claudeAiOauth', {})
print(oauth.get('accessToken', ''))
")

EXPIRES_AT=$(python3 -c "
import json, datetime
d = json.load(open('$CREDS_FILE'))
oauth = d.get('claudeAiOauth', {})
exp_ms = oauth.get('expiresAt', 0)
exp_dt = datetime.datetime.fromtimestamp(exp_ms/1000).strftime('%Y-%m-%d %H:%M:%S')
print(exp_dt)
")

if [[ -z "$FRESH_TOKEN" ]]; then
  log "ERROR: No access token in Claude Code credentials"
  exit 1
fi

log "Found Claude Code token: ${FRESH_TOKEN:0:30}... (expires: $EXPIRES_AT)"

# Test if this token works against the Claude API (OAuth tokens may only work via claude CLI)
# Claude Code CLI always works — track its health instead
CLAUDE_HEALTHY="false"
if timeout 10 claude --print "ping" &>/dev/null; then
  CLAUDE_HEALTHY="true"
  log "Claude Code CLI: HEALTHY"
else
  log "Claude Code CLI: UNHEALTHY"
fi

# Write state
python3 -c "
import json, datetime
state = {
  'checked_at': datetime.datetime.now().isoformat(),
  'claude_cli_healthy': $([[ $CLAUDE_HEALTHY == 'true' ]] && echo 'True' || echo 'False'),
  'token_prefix': '${FRESH_TOKEN:0:30}',
  'token_expires': '$EXPIRES_AT'
}
json.dump(state, open('$STATE_FILE', 'w'), indent=2)
print('State written to $STATE_FILE')
"

log "Done."
