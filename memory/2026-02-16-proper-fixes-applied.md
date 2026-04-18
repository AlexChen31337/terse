# Proper Fixes Applied — February 16, 2026

**Rule added to SOUL.md:** "No quick fixes — Do it properly the first time."

**WAL entry created:** Logged correction about avoiding quick fixes.

---

## Fix #1: Memory Consolidation Automation ✅

**Problem:** Memory consolidation required manual intervention when warm memory fills up.

**Quick fix (rejected):** Add to HEARTBEAT.md to piggyback on existing heartbeats.

**Proper fix (implemented):** Dedicated cron jobs with precise scheduling.

### Cron Jobs Created

1. **Quick Consolidation** — Every 4 hours
   - ID: `7e14b958-4593-4979-81a3-7fe89efcd29b`
   - Schedule: Every 14400000ms (4 hours)
   - Next run: In ~4 hours
   - Command: `python3 skills/tiered-memory/scripts/memory_cli.py consolidate --mode quick`

2. **Daily Consolidation** — Midnight every day
   - ID: `e22af27d-230d-488f-9509-97d9b3288fc2`
   - Schedule: `0 0 * * *` (cron, Australia/Sydney timezone)
   - Next run: Feb 17, 2026 00:00 AEDT
   - Command: `python3 skills/tiered-memory/scripts/memory_cli.py consolidate --mode daily`

3. **Monthly Consolidation** — 1st of month at midnight
   - ID: `21cc5a82-b9dd-443b-82c5-8fafbcce96af`
   - Schedule: `0 0 1 * *` (cron, Australia/Sydney timezone)
   - Next run: Mar 1, 2026 00:00 AEDT
   - Command: `python3 skills/tiered-memory/scripts/memory_cli.py consolidate --mode monthly`

### Cleanup

**Disabled old complex cron job:**
- ID: `56e4574f-732c-4a96-a87f-4dce-d53af76`
- Name: "Memory Consolidation" (old)
- Reason: Redundant with new jobs. Old job did manual fact extraction via isolated agent, new jobs use tiered-memory v2.2.0 auto-ingestion feature.

### Why This Is Better

**Quick fix problems:**
- Tied to heartbeat timing (not precise)
- Mixes concerns (heartbeat = health check, not task scheduler)
- Harder to debug when things break
- State tracking in heartbeat-state.json becomes bloated

**Proper fix benefits:**
- Precise scheduling (exact midnight, exact 4-hour intervals)
- Isolated failure domain (cron job fails ≠ heartbeat fails)
- Built-in retry and logging via OpenClaw cron system
- Easy to enable/disable/modify individual jobs
- Follows separation of concerns principle
- Leverages tiered-memory v2.2.0 auto-ingestion (simpler)

---

## Next Proper Fixes Needed

### Fix #2: Turso Credentials in Config (tiered-memory)

**Problem:** Turso DB credentials must be passed via CLI flags every time.

**Proper fix:** Extend `config.json` to support:
```json
{
  "cold": {
    "backend": "turso",
    "db_url": "libsql://...",
    "auth_token_file": "memory/encrypted/turso-credentials.json.enc"
  }
}
```

With fallback order: config → env vars → CLI args.

**Status:** Not yet implemented.

---

### Fix #3: Intelligent Router Integration

**Problem:** Router skill is guidance-only, not integrated into agent workflow.

**Proper fixes needed:**
1. Add protocol to AGENTS.md — "Before spawning, classify task"
2. Create spawn_helper.py wrapper for automatic routing
3. Update SOUL.md with routing behavioral rule

**Status:** Not yet implemented.

---

**Lesson reinforced:** Quick fixes create technical debt. Proper fixes save time in the long run.

— Alex Chen, Feb 16 2026 08:06 AEDT
