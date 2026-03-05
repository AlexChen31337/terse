# HEARTBEAT.md
## Blog & Feed Monitor (every 4h, during active hours)

### RSS feeds (blogwatcher)
```bash
export PATH="$PATH:$(go env GOPATH)/bin"
blogwatcher scan 2>&1
```
Working feeds: Bitcoin Magazine, Hacker News ✅
Alert only if 3+ new articles and at least one is clearly relevant (AI models, crypto, agent tech).

### GitHub intelligence (gh CLI)
```bash
# ClawInfra releases — check for new releases since last check
gh api /repos/clawinfra/claw-chain/releases?per_page=3 2>/dev/null | python3 -c "import sys,json,datetime; rs=json.load(sys.stdin); [print(r['tag_name'], r['published_at']) for r in rs]"
gh api /repos/clawinfra/evoclaw/releases?per_page=3 2>/dev/null | python3 -c "import sys,json; rs=json.load(sys.stdin); [print(r['tag_name'], r['published_at']) for r in rs]"

# Trending AI agent repos (weekly pulse)
gh api "/search/repositories?q=ai+agent+framework+pushed:>$(date -d '7 days ago' +%Y-%m-%d)&sort=stars&order=desc&per_page=5" 2>/dev/null | python3 -c "import sys,json; [print(r['full_name'], r['stargazers_count'], (r['description'] or '')[:70]) for r in json.load(sys.stdin)['items']]"

# Open PRs across clawinfra
gh pr list --repo clawinfra/claw-chain --state open --limit 5 2>/dev/null
gh pr list --repo clawinfra/evoclaw --state open --limit 5 2>/dev/null
```
Alert Bowen if: new clawinfra release detected, or trending repo clearly competitive with EvoClaw/ClawChain.

## CI Pipeline Monitor (every heartbeat)
Check Gmail for GitHub Actions failure notifications:
1. Search inbox for unread GitHub Actions failure emails: subject "Run failed" or "workflow run failed"
2. If found: read the failure details, clone/cd to the repo, fix locally, push
3. Mark email as read after fixing
4. If fix is non-trivial, alert Bowen

## Session Context Hydration (every heartbeat)
Prevent context_loss for long-running session_management tasks:
1. Check `memory/active_task.json` — if a task is in-flight, log current step to WAL before proceeding
2. If session was recently compacted (check `memory/2026-*.md` for today), re-read SOUL.md + USER.md to restore persona
3. **Critical context pre-fetch:** Before any session_management work, always read:
   - SOUL.md (persona and autonomy rules)
   - AGENTS.md (workspace protocols)
   - Most recent memory note (today or yesterday)
4. For any multi-step task >5min, ensure WAL entry exists: `uv run python skills/agent-self-governance/scripts/wal.py append main session_management "<current state>"`

## Pre-Push Gate (NON-NEGOTIABLE — learned 2026-03-04)
Before ANY git push to a repo with CI:
1. Run full test suite locally and confirm pass
2. Run lint locally and confirm clean
3. If fixing a bug: reproduce the bug locally FIRST, then fix, then verify fix kills it
Never push "I think it's fine" — prove it locally.

## context_loss Prevention (RSI pattern: 55x failures)
Before any multi-step task or session_management work:
1. Check active task: `uv run python scripts/active_task.py resume`
2. If task in-flight, log WAL before proceeding
3. After every major step in a long task, update: `uv run python scripts/active_task.py update --step "..."`
4. Unknown/uncategorised tasks (77x `none` outcomes) — always tag task type when logging to RSI

## tool_error Prevention (RSI pattern: 59x failures in tool_call tasks)
Root cause: subagents importing `claude_agent_sdk` without mocking — fails immediately.
Prevention rules:
- **Any subagent task touching claw_forge/ code** must include at top of test files:
  ```python
  import sys, unittest.mock
  sys.modules['claude_agent_sdk'] = unittest.mock.MagicMock()
  sys.modules['claude_agent_sdk.types'] = unittest.mock.MagicMock()
  ```
- **Before spawning a subagent** that runs pytest: verify the task prompt includes the mock instruction
- **On tool_error in a subagent**: first check if it's a missing import — add mock and retry
- Log tool_error outcomes: `uv run python skills/rsi-loop/scripts/rsi_cli.py log --task tool_call --issue tool_error --success false`

## RSI Loop Health (every 4+ hours)
If 4+ hours since last RSI check:
1. Run cycle: `cd ~/.openclaw/workspace && uv run python skills/rsi-loop/scripts/rsi_cli.py cycle --auto`
2. Check health: `cd ~/.openclaw/workspace && uv run python skills/rsi-loop/scripts/rsi_cli.py status`
3. Run shim scan: `cd ~/.openclaw/workspace && uv run python skills/rsi-loop/scripts/openclaw_shim.py scan --since 4h`
4. If health score < 0.3, alert Bowen
5. Deploy any safe proposals automatically
6. Update lastRSICheck timestamp in memory/heartbeat-state.json
## Handling Inbound Agent Reports
When the following system messages arrive in the main session, handle them as Alex — synthesise and filter before surfacing to Bowen:

**[NightlyHealth]** — from Nightly Health cron:
- Parse statuses. If ALL green → do NOT disturb Bowen, just log to memory
- If any issue (DOWN, offline, error) → notify Bowen concisely: "🌙 Morning check: [issue summary]"

**[MidnightAlpha]** — from Midnight Alpha cron:
- Always surface to Bowen with a short teaser (it's research for him, worth his attention)
- Format: "🌙 Midnight Alpha ready — [Top pick: X]. Ask me to share it."
- Do NOT paste the full report unprompted

**[Quant]**, **[Sentinel]**, **[Supervision]** — from agent monitoring crons:
- Only surface to Bowen if actionable (service DOWN, critical alert)
- Routine status → log to memory, stay quiet
