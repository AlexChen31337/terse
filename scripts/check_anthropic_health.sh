#!/usr/bin/env bash
# Check Anthropic OAuth health — outputs JSON result
# Used by heartbeat cron to detect when to route via Claude Code
set -euo pipefail

STATE_FILE="$HOME/.openclaw/workspace/memory/oauth-health.json"

probe_direct_api() {
  # Test openclaw's direct anthropic/ provider (reads token from openclaw config)
  TOKEN=$(node -e "
    const fs = require('fs');
    const raw = fs.readFileSync('/home/bowen/.openclaw/openclaw.json','utf8');
    const c = JSON.parse(raw);
    // Find anthropic provider's token
    const providers = c?.models?.providers || {};
    const ap = providers['anthropic'] || {};
    console.log(ap.apiKey || c?.env?.ANTHROPIC_SETUP_TOKEN || '');
  " 2>/dev/null || echo "")

  if [[ -z "$TOKEN" ]]; then
    echo "unknown"
    return
  fi

  HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 8 \
    -H "anthropic-version: 2023-06-01" \
    -H "x-api-key: $TOKEN" \
    -H "content-type: application/json" \
    -d '{"model":"claude-haiku-4-5","max_tokens":5,"messages":[{"role":"user","content":"hi"}]}' \
    "https://api.anthropic.com/v1/messages" 2>/dev/null || echo "000")
  echo "$HTTP"
}

probe_proxy1() {
  TOKEN=$(node -e "
    const fs = require('fs');
    const raw = fs.readFileSync('/home/bowen/.openclaw/openclaw.json','utf8');
    const c = JSON.parse(raw);
    const providers = c?.models?.providers || {};
    const p1 = providers['anthropic-proxy-1'] || {};
    console.log(p1.apiKey || '');
  " 2>/dev/null || echo "")

  if [[ -z "$TOKEN" ]]; then
    echo "unknown"
    return
  fi

  HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 8 \
    -H "anthropic-version: 2023-06-01" \
    -H "x-api-key: $TOKEN" \
    -H "content-type: application/json" \
    -d '{"model":"claude-haiku-4-5","max_tokens":5,"messages":[{"role":"user","content":"hi"}]}' \
    "https://api.anthropic.com/v1/messages" 2>/dev/null || echo "000")
  echo "$HTTP"
}

probe_claude_cli() {
  if timeout 10 claude --print "ok" &>/dev/null 2>&1; then
    echo "ok"
  else
    echo "fail"
  fi
}

# Run probes
DIRECT=$(probe_direct_api)
PROXY1=$(probe_proxy1)
CLI=$(probe_claude_cli)

# Determine status
DIRECT_OK=false
PROXY1_OK=false
CLI_OK=false

[[ "$DIRECT" == "200" ]] && DIRECT_OK=true
[[ "$PROXY1" == "200" ]] && PROXY1_OK=true
[[ "$CLI" == "ok" ]] && CLI_OK=true

python3 -c "
import json, datetime

state = {
  'checked_at': datetime.datetime.now().isoformat(),
  'direct_api': {'status': '$DIRECT', 'healthy': $([[ $DIRECT_OK == 'true' ]] && echo 'True' || echo 'False')},
  'proxy1_api': {'status': '$PROXY1', 'healthy': $([[ $PROXY1_OK == 'true' ]] && echo 'True' || echo 'False')},
  'claude_cli': {'status': '$CLI', 'healthy': $([[ $CLI_OK == 'true' ]] && echo 'True' || echo 'False')},
  'recommendation': 'proxy1' if $([[ $PROXY1_OK == 'true' ]] && echo 'True' || echo 'False') else ('claude_code_cli' if $([[ $CLI_OK == 'true' ]] && echo 'True' || echo 'False') else 'degraded')
}

if not state['direct_api']['healthy'] and state['proxy1_api']['healthy']:
  state['alert'] = 'ANTHROPIC_OAUTH_EXPIRED: Direct OAuth down, proxy-1 active (fallback working)'
elif not state['direct_api']['healthy'] and not state['proxy1_api']['healthy'] and state['claude_cli']['healthy']:
  state['alert'] = 'ANTHROPIC_ALL_API_DOWN: Route ALL tasks via Claude Code CLI (sessions_spawn runtime=acp or exec claude --print)'
elif not state['direct_api']['healthy'] and not state['proxy1_api']['healthy'] and not state['claude_cli']['healthy']:
  state['alert'] = 'ANTHROPIC_TOTAL_OUTAGE: All Anthropic capacity down. Notify Bowen immediately.'
else:
  state['alert'] = None

with open('$STATE_FILE', 'w') as f:
  json.dump(state, f, indent=2)

print(json.dumps(state, indent=2))
"
