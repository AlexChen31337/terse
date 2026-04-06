#!/usr/bin/env bash
# Probe Anthropic OAuth — returns 0 if healthy, 1 if failing
# Usage: ./probe_anthropic_oauth.sh [timeout_seconds]
set -euo pipefail

TIMEOUT=${1:-10}
TOKEN_FILE="/home/bowen/.openclaw/workspace/memory/encrypted/local-sudo.enc"

# Read OAuth token from env (OpenClaw injects it at runtime, so test via API)
OAUTH_TOKEN="${ANTHROPIC_SETUP_TOKEN:-}"

if [[ -z "$OAUTH_TOKEN" ]]; then
  # Try reading from openclaw config
  OAUTH_TOKEN=$(node -e "
    const fs = require('fs');
    try {
      const c = JSON.parse(fs.readFileSync('/home/bowen/.openclaw/openclaw.json','utf8'));
      const p = c?.models?.providers?.anthropic || c?.env;
      // Just test via the env
      console.log(c?.env?.ANTHROPIC_SETUP_TOKEN || '');
    } catch(e) { console.log(''); }
  " 2>/dev/null || echo "")
fi

if [[ -z "$OAUTH_TOKEN" ]]; then
  echo "PROBE_ERROR: No OAuth token available"
  exit 2
fi

# Minimal probe — list models endpoint (cheap, no tokens used)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  --max-time "$TIMEOUT" \
  -H "anthropic-version: 2023-06-01" \
  -H "authorization: Bearer $OAUTH_TOKEN" \
  "https://api.anthropic.com/v1/models" 2>/dev/null || echo "000")

if [[ "$HTTP_CODE" == "200" ]]; then
  echo "OAUTH_OK: HTTP $HTTP_CODE"
  exit 0
elif [[ "$HTTP_CODE" == "401" ]] || [[ "$HTTP_CODE" == "403" ]]; then
  echo "OAUTH_AUTH_FAIL: HTTP $HTTP_CODE — token expired or invalid"
  exit 1
elif [[ "$HTTP_CODE" == "429" ]]; then
  echo "OAUTH_RATE_LIMITED: HTTP $HTTP_CODE — quota exhausted"
  exit 1
elif [[ "$HTTP_CODE" == "000" ]]; then
  echo "OAUTH_TIMEOUT: connection failed or timed out"
  exit 1
else
  echo "OAUTH_DEGRADED: HTTP $HTTP_CODE"
  exit 1
fi
