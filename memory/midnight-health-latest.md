# Midnight Health Report
**Generated:** 2026-03-31 00:00 AEDT (2026-03-30 13:00 UTC)
**Run by:** Sentinel (cron job)

---

## Summary

| Component | Status | Notes |
|---|---|---|
| Sentinel | ✅ OK | 1 alert in last 24h |
| Quant State | ⚠️ STALE | Last check 2026-03-26 (5 days ago) |
| AlphaStrike | 🔴 DOWN | WorkDir missing: `/media/DATA/tmp/alphastrike-v2` |
| Shield | ⚠️ MISSING | `access-control.json` not found |
| Herald | ✅ OK | No activity (fresh state) |
| EvoClaw Hub (:8420) | 🔴 DOWN | MQTT broker (mosquitto) not running |
| Alex Eye (Pi) | 🔴 DOWN | SSH unreachable (alexeye.local / raspberrypi.local) |

---

## 1. Sentinel
- **Status:** ✅ OK
- **Last prices:** BTC $67,887 | ETH $2,073 | SOL $84.53 | HYPE $38.25
- **Fear & Greed:** Extreme Fear (8)
- **Last price check:** Recent (within normal window)
- **Alerts last 24h:** 1 — `btc_67500` at 22:17

## 2. Quant / AlphaStrike
- **Quant state:** ⚠️ STALE — last check was 2026-03-26T01:21 UTC (5 days ago, signals outdated)
- **Account value:** $112.22 | Today P&L: $0.00 | Open positions: 0
- **AlphaStrike service:** 🔴 DOWN
  - Error: `Failed to spawn 'start' task: No such file or directory`
  - Root cause: WorkDir `/media/DATA/tmp/alphastrike-v2` does not exist
  - `/media/DATA` IS mounted (shows data) but `tmp/alphastrike-v2` directory is missing
  - The directory may have been deleted or never recreated after a reboot

## 3. Shield
- **Status:** ⚠️ MISSING
- `access-control.json` not found at `/home/bowen/.openclaw/workspace-shield/`
- No pending approvals detected (file absent)

## 4. Herald
- **Status:** ✅ OK (idle)
- State: empty/fresh (no posts, no outreach, no alerts)

## 5. EvoClaw Hub (:8420)
- **Status:** 🔴 DOWN — restart failed
- Root cause: MQTT broker (mosquitto) not running (inactive/not installed)
- Error: `connect: connection refused` on `tcp://0.0.0.0:1883`
- `evoclaw-hub.service` is enabled but failed
- **Fix needed:** Start mosquitto service or configure EvoClaw to skip MQTT

## 6. Alex Eye (Pi)
- **Status:** 🔴 DOWN
- SSH unreachable at `alexeye.local` and `raspberrypi.local`
- Cannot restart remotely — requires physical check or network investigation

---

## Actions Taken
- Attempted `systemctl --user restart evoclaw-hub.service` → FAILED (MQTT dependency)
- Telegram alert sent to Bowen (2069029798) for all DOWN components

---

## Disk Status
- `/`: 560G used / 937G total (63%) — OK
- `/media/DATA`: mounted, has content (playwright profiles, clawd dir)
- `/data2`: not mounted / not present
