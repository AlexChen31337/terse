# HEARTBEAT.md
## Session Wake Detection (ALWAYS RUN FIRST — every heartbeat)
Detect if this is a new session (reset/restart) and hydrate if so:
1. Run: `bash memory/scripts/check_new_session.sh`
- Output format: `CURRENT_ID|STORED_ID`
- Exit 0 = same session, Exit 1 = new session
2. If NEW session (exit 1):
  a. **Run hydration immediately:**
    - Read `memory/$(date +%Y-%m-%d).md` (today's daily notes)
    - Read `memory/$(date -d 'yesterday' +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d).md` (yesterday)
    - **CRITICAL: Search tiered memory FIRST** (prevents WAL misses):
      ```bash
      uv run python skills/tiered-memory/scripts/memory_cli.py retrieve --query "config credentials agents projects decisions" --limit 10
      ```
    - Search hybrid memory: `uv run python skills/hybrid-memory/scripts/hybrid_cli.py search "recent projects decisions credentials" --limit 10`
    - Synthesize key context from MEMORY.md + retrieved results
  b. Update session ID: `uv run python memory/scripts/update_session_id.py <CURRENT_ID>`
  c. Write a brief "Session restarted, context reloaded" note to today's daily file
  d. Notify Bowen: "🔄 Session reset detected — I've reloaded context. Here's what I remember: [brief summary]"
3. If SAME session: continue to other checks below.
## RSI Loop Health (every 4+ hours)
If 4+ hours since last RSI check:
1. Run cycle: `cd ~/clawd && uv run python skills/rsi-loop/scripts/rsi_cli.py cycle --auto`
2. Check health: `cd ~/clawd && uv run python skills/rsi-loop/scripts/rsi_cli.py status`
3. Run shim scan: `cd ~/clawd && uv run python skills/rsi-loop/scripts/openclaw_shim.py scan --since 4h`
4. If health score < 0.3, alert Bowen
5. Deploy any safe proposals automatically
6. Update lastRSICheck timestamp in memory/heartbeat-state.json
## Hybrid Memory Reindex (every 12 hours)
If 12+ hours since last hybrid memory reindex:
1. Reindex: `cd ~/clawd && uv run python skills/hybrid-memory/scripts/hybrid_cli.py ingest-memory`
2. Check stats: `cd ~/clawd && uv run python skills/hybrid-memory/scripts/hybrid_cli.py stats`
3. Update lastHybridMemoryReindex timestamp in memory/heartbeat-state.json
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
Check position guard status: `cd ~/clawd && uv run python skills/simmer-risk/position_guard.py status`
