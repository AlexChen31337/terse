# HEARTBEAT.md

## Blog & Feed Monitor (every 4h, active hours)
```bash
export PATH="$PATH:$(go env GOPATH)/bin"
blogwatcher scan 2>&1
```
Alert if 3+ relevant new articles (AI models, crypto, agent tech).

## GitHub Intelligence
```bash
gh api /repos/clawinfra/claw-chain/releases?per_page=3 2>/dev/null | python3 -c "import sys,json; [print(r['tag_name'], r['published_at']) for r in json.load(sys.stdin)]"
gh pr list --repo clawinfra/claw-chain --state open --limit 5 2>/dev/null
gh pr list --repo clawinfra/evoclaw --state open --limit 5 2>/dev/null
```

## CI Monitor
Check Gmail for GitHub Actions failures. Fix locally if trivial, alert Bowen if not.

## Context Hydration
Check `memory/active_task.json`. If task in-flight, log WAL. Re-read SOUL.md/AGENTS.md after compaction.

## Pre-Push Gate (NON-NEGOTIABLE)
Run tests + lint locally before ANY push. Never push "I think it's fine".

## RSI Prevention Rules
- **tool_validation_error:** Never angle brackets in tool calls. Add to all sub-agent prompts: "Use tool names exactly as listed. Never wrap in angle brackets."
- **timeout:** Set `yieldMs` or `background=true` for exec >10s. SSH: explicit timeout.
- **tool_error:** Mock `claude_agent_sdk` in subagent test tasks.
- **context_loss:** Check active_task.py resume. Log WAL before long tasks.

## Anthropic OAuth Health & Claude Code Routing

Cron fires every 4 hours in an **isolated** session (GLM-4.7) — NOT main session.

**On health check event (isolated cron handles this automatically):**
1. Run `bash /home/bowen/.openclaw/workspace/scripts/check_anthropic_health.sh`
2. Read `memory/oauth-health.json` for result
3. Act on `alert` field:

| Alert | Action |
|-------|--------|
| `null` | HEARTBEAT_OK — log silently |
| `OAUTH_EXPIRED` | Notify Bowen. Fallback `anthropic-proxy-1/` is active. No action needed. |
| `ALL_API_DOWN` | **Immediately**: route ALL Anthropic tasks through Claude Code CLI |
| `TOTAL_OUTAGE` | Alert Bowen urgently via **Telegram only** (never WhatsApp). Suggest re-auth: `openclaw auth` |

**⚠️ All notifications: Telegram only. Never push to WhatsApp channel.**

**Claude Code CLI routing (when API is down):**
```bash
# For quick tasks
claude --print --permission-mode bypassPermissions 'your task here'

# For coding/sub-agent tasks (ACP harness)
sessions_spawn(runtime="acp", agentId="claude-code", task="your task")
```

**Re-auth fix (when OAuth expired):**
```bash
openclaw auth  # Re-links the Anthropic OAuth token
```
After re-auth: Claude Code CLI's fresh token is in `~/.claude/.credentials.json`.
Two OAuth tokens = two quotas: OpenClaw direct API + Claude Code Pro subscription.

## Agent Report Handling
- **[NightlyHealth]:** All green → log silently. Issue → notify Bowen concisely.
- **[MidnightAlpha]:** Always surface teaser to Bowen.
- **[Sentinel/Quant/Supervision]:** Only surface if actionable (DOWN, critical). Routine → log silently.
