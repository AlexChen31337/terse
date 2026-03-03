# HEARTBEAT.md
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
