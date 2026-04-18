# Comm Watchdog — Cron Task Prompt

Run the communication watchdog to check for new emails and surface actionable ones.

## Steps

1. Run the watchdog script:
```bash
cd /home/bowen/.openclaw/workspace
uv run python scripts/comm_watchdog.py 2>&1
```

2. Check if there are pending notifications to deliver:
```bash
cat memory/comm-watchdog-pending.json 2>/dev/null
```

3. If pending notifications exist:
   - Send each message to Bowen via `sessions_send(sessionKey="agent:main:main", message=<notification>)`
   - Clear the file: `echo "[]" > memory/comm-watchdog-pending.json`

4. Log completion to WAL if any actionable items were found.

## Notes
- Quarantined = spam/bots: auto-marked read, no notification
- Noise = irrelevant GitHub notifications: auto-marked read, no notification  
- Actionable = real emails from real people or about our repos: surface to Bowen
- Ask = ambiguous: batch and ask Bowen to decide
