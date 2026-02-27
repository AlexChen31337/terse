# HEARTBEAT.md
## CI Pipeline Monitor (every heartbeat)
Check Gmail for GitHub Actions failure notifications:
1. Search inbox for unread GitHub Actions failure emails: subject "Run failed" or "workflow run failed"
2. If found: read the failure details, clone/cd to the repo, fix locally, push
3. Mark email as read after fixing
4. If fix is non-trivial, alert Bowen

## RSI Loop Health (every 4+ hours)
If 4+ hours since last RSI check:
1. Run cycle: `cd ~/.openclaw/workspace && uv run python skills/rsi-loop/scripts/rsi_cli.py cycle --auto`
2. Check health: `cd ~/.openclaw/workspace && uv run python skills/rsi-loop/scripts/rsi_cli.py status`
3. Run shim scan: `cd ~/.openclaw/workspace && uv run python skills/rsi-loop/scripts/openclaw_shim.py scan --since 4h`
4. If health score < 0.3, alert Bowen
5. Deploy any safe proposals automatically
6. Update lastRSICheck timestamp in memory/heartbeat-state.json
## Simmer Prediction Markets (every 4+ hours)
If 4+ hours since last Simmer check:
1. Health check: `curl -s https://api.simmer.markets/api/sdk/health`
2. Load key: `SIMMER_API_KEY=$(uv run python -c "import json; print(json.load(open('$HOME/.config/simmer/credentials.json'))['api_key'])")`
3. Get briefing: `curl -s "https://api.simmer.markets/api/sdk/briefing?since=<last_check_iso>" -H "Authorization: Bearer $SIMMER_API_KEY"`
4. Check `risk_alerts` — act on any urgent warnings immediately
5. Check `positions.expiring_soon` — exit or hold before resolution?
6. Check `positions.significant_moves` — reassess thesis on >15% movers
7. Check `opportunities.high_divergence` — AI price vs market price gaps
8. Check `opportunities.new_markets` — anything worth trading?
9. Note `performance.rank` — climbing or falling?
10. Update lastSimmerCheck timestamp in memory/heartbeat-state.json
11. If anything notable (big move, expiring position, good opportunity) → alert Bowen
All positions closed as of 2026-02-22. Risk framework at skills/simmer-risk/ must be active before any new trades.
Check position guard status: `cd ~/.openclaw/workspace && uv run python skills/simmer-risk/position_guard.py status`

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
