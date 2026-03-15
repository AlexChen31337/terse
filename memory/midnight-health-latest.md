# Midnight Health Check Report
**Generated:** 2026-03-16 00:00 AEDT (2026-03-15 13:00 UTC)

---

## 1. Sentinel ✅
- **Status:** ACTIVE
- **Last Price Check:** 2026-03-15 12:30 UTC (2h ago)
- **Recent Alerts (24h):**
  - BTC crossed $75,000 (alert at 1773616194)
  - Fear & Greed: Extreme Fear (15) — alert sent
  - HYPE at $37.44 (above $30 threshold)
- **State File:** `/home/bowen/.openclaw/workspace-sentinel/memory/sentinel-state.json` — OK
- **Verdict:** HEALTHY

## 2. Quant ✅
- **Status:** ACTIVE
- **AlphaStrike Service:** `active` (systemd user service running)
- **Account Value:** $112.22
- **Strategy:** Hyperliquid perps, no Simmer
- **Open Positions:** None
- **Current Signals:**
  - BTC: SHORT @ $71,730 (confidence 0.4 — HOLD)
  - ETH: SHORT @ $2,118 (confidence 0.4 — HOLD)
  - SOL: SHORT @ $88.29 (confidence 0.4 — HOLD)
- **Last Checks:** 2026-03-15 11:21 UTC
- **FearHarvester:** Last run 2026-02-27 (stale — needs investigation)
- **Verdict:** HEALTHY (but FearHarvester stale)

## 3. Shield ⚠️
- **Access Control File:** `/home/bowen/.openclaw/access-control.json` — NOT FOUND
- **Pending Approvals:** Cannot check (file missing)
- **Verdict:** NEEDS ATTENTION — access-control.json missing

## 4. Herald ✅
- **Status:** IDLE (no recent activity)
- **State File:** `/home/bowen/.openclaw/workspace-herald/memory/herald-state.json` — OK
- **Scheduled Posts:** None
- **Outreach Log:** Empty
- **Verdict:** HEALTHY (no active campaigns)

## 5. EvoClaw Hub ❌
- **API Check:** `curl http://localhost:8420/api/agents` — FAILED (HUB_DOWN)
- **Service Status:** `evo-hub.service` not found
- **Process Check:** No hub process running
- **Action Required:** Restart EvoClaw Hub
- **Verdict:** DOWN

## 6. Alex Eye (Pi) ⏸️
- **SSH Check:** Timed out (ALEXEYE_DOWN)
- **Host:** pi@192.168.1.100
- **Verdict:** DOWN (network or host issue)

---

## Disk Status
- `/`: 63% used (337G free of 937G) — OK
- `/media/DATA`: Not mounted
- `/data2`: Not mounted

## Summary
| Component | Status | Action Needed |
|---|---|---|
| Sentinel | ✅ OK | None |
| Quant | ✅ OK | Check FearHarvester (stale since Feb 27) |
| Shield | ⚠️ WARN | Recreate access-control.json |
| Herald | ✅ OK | None |
| EvoClaw Hub | ❌ DOWN | **RESTART REQUIRED** |
| Alex Eye (Pi) | ❌ DOWN | Check network/host |

## Critical Actions
1. **RESTART EvoClaw Hub** — not running, no systemd service found
2. **Check Alex Eye (Pi)** — network timeout, verify host is up
3. **Recreate Shield access-control.json** — missing file
4. **Investigate FearHarvester** — last run Feb 27, may need manual trigger

---

*Report saved to: `~/.openclaw/workspace/memory/midnight-health-latest.md`*
