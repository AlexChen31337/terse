# HEARTBEAT.md

## 🔁 Session Wake Detection (ALWAYS RUN FIRST — every heartbeat)
Detect if this is a new session (reset/restart) and hydrate if so:
1. Run: `bash memory/scripts/check_new_session.sh`
   - Output format: `CURRENT_ID|STORED_ID`
   - Exit 0 = same session, Exit 1 = new session
2. If NEW session (exit 1):
   a. **Run hydration immediately:**
      - Read `memory/$(date +%Y-%m-%d).md` (today's daily notes)
      - Read `memory/$(date -d 'yesterday' +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d).md` (yesterday)
      - Search tiered memory: `python3 skills/tiered-memory/scripts/memory_cli.py retrieve --query "recent projects decisions events" --limit 5`
      - Synthesize key context from MEMORY.md + retrieved results
   b. Update session ID: `python3 memory/scripts/update_session_id.py <CURRENT_ID>`
   c. Write a brief "Session restarted, context reloaded" note to today's daily file
   d. Notify Bowen: "🔄 Session reset detected — I've reloaded context. Here's what I remember: [brief summary]"
3. If SAME session: continue to other checks below.

## EvoClaw Hub + Eye Health (every 6 hours)
If 6+ hours since last EvoClaw check:
1. Hub API: `curl -s http://localhost:8420/api/agents | python3 -c "import sys,json; agents=json.load(sys.stdin); print(f'{len(agents)} agents registered')" 2>/dev/null || echo "HUB DOWN"`
2. Hub PID: `cat ~/.evoclaw-hub/evoclaw.pid 2>/dev/null && ps -p $(cat ~/.evoclaw-hub/evoclaw.pid) > /dev/null 2>&1 && echo "HUB OK" || echo "HUB DEAD"`
3. Eye SSH: `ssh -i ~/.ssh/id_ed25519_alexchen -o ConnectTimeout=5 admin@192.168.99.188 "pgrep evoclaw > /dev/null && echo 'EYE OK' || echo 'EYE DOWN'"`
4. Eye MQTT: `ssh -i ~/.ssh/id_ed25519_alexchen -o ConnectTimeout=5 admin@192.168.99.188 "nc -z -w2 192.168.99.44 1883 && echo 'MQTT OK' || echo 'MQTT DOWN'"`
5. If Hub DOWN: restart with `cd ~/.evoclaw-hub && bash start.sh`
6. If Eye DOWN: `ssh -i ~/.ssh/id_ed25519_alexchen admin@192.168.99.188 "cd ~/.evoclaw && bash start-agent.sh"`
7. Update lastEvoclawCheck timestamp in memory/heartbeat-state.json
8. Alert Bowen ONLY if restart fails

## GitHub Trending - Coding/Technical Models (every 12 hours)
Watch for:
- Open-source models good at technical data analysis
- Coding-focused models (code generation, debugging, analysis)
- New model releases or significant updates
Use GitHub API with token from memory/github-token.txt
Report interesting finds to Bowen

## Moltbook (every 4+ hours)
If 4+ hours since last Moltbook check:
1. Check for DMs: curl https://www.moltbook.com/api/v1/agents/dm/check -H "Authorization: Bearer $(memory/decrypt.sh moltbook-credentials.json | python3 -c 'import json,sys;print(json.load(sys.stdin)["api_key"])')"
2. Check feed: curl "https://www.moltbook.com/api/v1/feed?sort=new&limit=10" -H "Authorization: Bearer $(memory/decrypt.sh moltbook-credentials.json | python3 -c 'import json,sys;print(json.load(sys.stdin)["api_key"])')"
3. Look for: mentions, interesting posts, DM requests
4. Update lastMoltbookCheck timestamp in memory/heartbeat-state.json

## GitHub (every 24 hours)
If 24+ hours since last GitHub check:
1. Check notifications: gh notification list
2. Update lastGitHubCheck timestamp in memory/heartbeat-state.json

## Twitter (every 2+ hours)
If 2+ hours since last Twitter check:
1. Export auth: AUTH_TOKEN and CT0 from `memory/decrypt.sh twitter-bird-credentials.txt`
2. Check mentions: `bird search "to:AlexChen31337" -n 5`
3. Check thread engagement: `bird search "from:AlexChen31337" -n 5`
4. Respond to relevant comments about ClawChain
5. Update lastTwitterCheck timestamp in memory/heartbeat-state.json
6. Report significant engagement or questions to Bowen

## KOL Market Monitoring (every 1+ hour) 🚨 PRIORITY
If 1+ hour since last KOL check:
1. Export auth: AUTH_TOKEN and CT0 from `memory/decrypt.sh twitter-bird-credentials.txt`
2. Monitor KOLs: `bird search "from:elonmusk" -n 3`, `bird search "from:VitalikButerin" -n 3`, etc.
3. Look for: crypto/stock market moving tweets from Elon, Vitalik, CZ, Saylor, etc.
4. Alert keywords: Bitcoin, ETH, SEC, regulation, crash, Fed, interest rates
5. **ALERT IMMEDIATELY if market-moving content found**
6. Update lastKOLCheck timestamp in memory/heartbeat-state.json

## Simmer Prediction Markets (every 4+ hours)
If 4+ hours since last Simmer check:
1. Health check: `curl -s https://api.simmer.markets/api/sdk/health`
2. Load key: `SIMMER_API_KEY=$(python3 -c "import json; print(json.load(open('$HOME/.config/simmer/credentials.json'))['api_key'])")`
3. Get briefing: `curl -s "https://api.simmer.markets/api/sdk/briefing?since=<last_check_iso>" -H "Authorization: Bearer $SIMMER_API_KEY"`
4. Check `risk_alerts` — act on any urgent warnings immediately
5. Check `positions.expiring_soon` — exit or hold before resolution?
6. Check `positions.significant_moves` — reassess thesis on >15% movers
7. Check `opportunities.high_divergence` — AI price vs market price gaps
8. Check `opportunities.new_markets` — anything worth trading?
9. Note `performance.rank` — climbing or falling?
10. Update lastSimmerCheck timestamp in memory/heartbeat-state.json
11. If anything notable (big move, expiring position, good opportunity) → alert Bowen
