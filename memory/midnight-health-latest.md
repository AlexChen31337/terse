# Midnight Health Report
**Generated:** 2026-03-30 00:00 AEDT (Australia/Sydney)

---

## Summary

| Component | Status | Notes |
|---|---|---|
| Sentinel | ✅ OK | Active, last check ~24h ago |
| AlphaStrike | ✅ RUNNING | Cycle 54 at 23:59 |
| Quant State | ⚠️ STALE | FearHarvester last run 2026-02-27 (31 days ago) |
| Shield | ✅ OK | State clean, no blocked attempts |
| Herald | ✅ OK | Idle, no active campaigns |
| EvoClaw Hub | 🔴 DOWN | MQTT broker (mosquitto) not installed — hub fails to start |
| Alex Eye (Pi) | 🔴 UNREACHABLE | No response on .local or known IPs |

---

## 1. Sentinel

- **State:** Active
- **Last Price Check:** timestamp 1774788362 (~24h ago)
- **Last Prices:** BTC $66,714 | ETH $1,998 | SOL $82.22 | HYPE $39.18
- **Fear & Greed:** Extreme Fear (9/100) — unchanged since last check
- **Recent Alerts Fired:** btc_65000, btc_60000, hype_25, hype_30 (all fired ~18–24h ago)
- **No new alerts in last 24h** — market appears stable at low levels

---

## 2. Quant / AlphaStrike

- **AlphaStrike Service:** ✅ `active` (systemd user service)
- **Last Log:** Cycle 54 at 23:59:58 — Balance $10,000 | 0 positions | 0 trades
- **Account Value (state):** $112.22 (Hyperliquid paper account)
- **Open Positions:** None
- **Last Signals:** BTC/ETH/SOL all LONG @ confidence 0.4 (dated 2026-03-26)
- **⚠️ FearHarvester:** Last run **2026-02-27** — 31 days stale. Not running.

---

## 3. Shield

- **access-control.json:** Not found at workspace-shield root (file not configured yet)
- **shield-state.json:** Clean — 0 blocked attempts, no active alerts
- **Status:** No issues detected; shield workspace minimal

---

## 4. Herald

- **State:** Idle
- **Last Posts:** None recorded
- **Scheduled Posts:** 0
- **Outreach Log:** Empty
- **Status:** Dormant, no active campaigns

---

## 5. EvoClaw Hub

- **Status:** 🔴 DOWN (failed to restart)
- **Root Cause:** `mosquitto` MQTT broker is not installed — hub requires it on `localhost:1883`
- **Port 8420:** Closed
- **Restart attempt:** Failed (exit code 1 — MQTT connect refused)
- **Fix required:** `sudo apt install mosquitto` — requires elevated permissions / manual action

---

## 6. Alex Eye (Pi)

- **Status:** 🔴 UNREACHABLE
- **Tried:** `alex-eye.local`, `raspberrypi.local`, IPs 10.0.0.50–52, 10.0.0.100, 192.168.1.50
- **All timed out / no response**
- **Action required:** Manual check / power cycle

---

## Disk

| Filesystem | Size | Used | Avail | Use% | Mount |
|---|---|---|---|---|---|
| /dev/nvme0n1p2 | 937G | 540G | 350G | 61% | / |
| /media/DATA | N/A | — | — | — | not mounted |
| /data2 | N/A | — | — | — | not mounted |

**Note:** /media/DATA and /data2 not accessible at check time.

---

## Actions Taken

- Attempted `systemctl --user start evoclaw-hub.service` → **failed** (MQTT dependency)
- Attempted SSH to Pi on all known addresses → **all unreachable**
- Telegam alert sent to Bowen for Hub + Pi

---

## Action Items for Bowen

1. **EvoClaw Hub:** Run `sudo apt install mosquitto && sudo systemctl enable --now mosquitto` to restore hub
2. **Alex Eye Pi:** Check power/network — Pi unreachable on all addresses
3. **FearHarvester:** Investigate why it stopped running (last: 2026-02-27) — may need cron restart or service fix
