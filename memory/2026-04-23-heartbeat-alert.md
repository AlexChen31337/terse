# Heartbeat Alert - Anthropic API Down

**Timestamp:** 2026-04-23 12:00 PM AEDT (2026-04-23 02:00 UTC)

## Status: CRITICAL

### Issue
Both Anthropic direct API and proxy1 are returning 401 errors.

### Health Check Results
```json
{
  "checked_at": "2026-04-23T12:00:48.180036",
  "direct_api": { "status": "401", "healthy": false },
  "proxy1_api": { "status": "401", "healthy": false },
  "claude_cli": { "status": "ok", "healthy": true },
  "recommendation": "claude_code_cli",
  "alert": "ANTHROPIC_ALL_API_DOWN: Route ALL tasks via Claude Code CLI"
}
```

### Actions Taken
1. ✅ WAL logged: `agent-wal append main heartbeat "Anthropic ALL_API_DOWN..."`
2. ✅ All tasks now routing via Claude Code CLI (per HEARTBEAT.md protocol)
3. ❌ Telegram alert NOT sent - Bot token not configured

### Required Action
Run `openclaw auth` to re-link OAuth tokens.

### Fallback Status
✅ **Operational** - Claude Code CLI is healthy and handling all tasks.

### Notes
- No service disruption expected
- Two OAuth tokens available: OpenClaw direct API + Claude Code Pro subscription
- Once re-authenticated, both quotas restore
