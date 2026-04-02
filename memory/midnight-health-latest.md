# Midnight Health Check — 2026-04-02 00:01 AEDT

**Run by:** Alex (Sentinel cron)
**Status:** ⚠️ 3 components DOWN

---

## 🔴 AlphaStrike — DOWN (restart failed)

- **Service:** `alphastrike.service` — `activating (auto-restart)` / Result: resources
- **Root cause:** Working directory `/media/DATA/tmp/alphastrike-v2` does not exist
  - Either `/media/DATA` is unmounted, or the directory was deleted
- **Action needed:** Remount DATA drive and verify alphastrike-v2 directory; or update service WorkingDirectory

---

## 🔴 EvoClaw Hub — DOWN (restart failed)

- **Service:** `evoclaw-hub.service` — exit-code failure
- **Root cause:** MQTT broker (mosquitto) is **inactive** / not running
  - Hub start.sh errors: `dial tcp 0.0.0.0:1883: connect: connection refused`
- **Cannot self-fix:** `mosquitto` requires `sudo systemctl start mosquitto` (system-level, needs password)
- **Action needed:** `sudo systemctl start mosquitto && sudo systemctl enable mosquitto`
  - Then retry: `systemctl --user restart evoclaw-hub.service`

---

## 🔴 Alex Eye (Pi) — UNREACHABLE

- SSH to `alexeye.local` → timeout
- SSH to `raspberrypi.local` → timeout
- **Status:** Pi is offline or not on network
- **Action needed:** Physical check or router ARP scan

---

## ✅ Sentinel

- Last price check: ~2h ago (1775047455)
- Prices: BTC $68,289 | ETH $2,126 | SOL $82.98 | HYPE $37.13
- Fear & Greed: **8 — Extreme Fear** (unchanged category)
- Last alerts: btc_67500, btc_65000, hype_25, hype_30 (within 24h window)
- No new thresholds crossed

---

## ✅ Shield (access-control.json)

- Owner numbers: 4 registered ✅
- Pending approvals: **none**
- Stranger response configured ✅

---

## ✅ Herald

- lastPosts: empty (no recent posts)
- scheduledPosts: none
- outreachLog: empty
- All checks at 0 (idle)

---

## ⚠️ Quant (quant-state.json)

- Status: ACTIVE (in state file)
- Account value: $112.22
- Open positions: none
- Signals: BTC/ETH/SOL all LONG @ confidence 0.4
- **Signal timestamp: 2026-03-26** — stale by ~7 days
- lastChecks.alphastrike: 1742915309 (2025-03-25) — very stale
- Trade log: empty (no trades executed)
- Action: Quant needs a manual heartbeat or reconnect

---

## 💾 Disk

| Mount | Size | Used | Avail | Use% |
|-------|------|------|-------|------|
| /     | 937G | 627G | 263G  | 71%  |

- `/media/DATA` — **not mounted** (no df output, alphastrike dir missing confirms this)
- `/data2` — not found

---

## Summary Table

| Component       | Status  | Auto-fixed? | Action Required |
|-----------------|---------|-------------|-----------------|
| Sentinel        | ✅ OK   | —           | None |
| Quant (state)   | ⚠️ Stale | —          | Manual heartbeat |
| Shield          | ✅ OK   | —           | None |
| Herald          | ✅ OK   | —           | None |
| AlphaStrike     | 🔴 DOWN | ❌ No       | Remount /media/DATA |
| EvoClaw Hub     | 🔴 DOWN | ❌ No       | sudo start mosquitto |
| Alex Eye (Pi)   | 🔴 DOWN | ❌ No       | Physical check |

---

*Bowen notified via Telegram.*
