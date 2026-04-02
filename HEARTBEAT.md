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

## Agent Report Handling
- **[NightlyHealth]:** All green → log silently. Issue → notify Bowen concisely.
- **[MidnightAlpha]:** Always surface teaser to Bowen.
- **[Sentinel/Quant/Supervision]:** Only surface if actionable (DOWN, critical). Routine → log silently.
