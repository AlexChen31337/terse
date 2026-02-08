# HEARTBEAT.md

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
