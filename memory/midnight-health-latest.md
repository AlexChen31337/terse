# Midnight Health Check Report
**Generated:** 2026-03-15 00:00:00 AEDT (2026-03-14 13:00:00 UTC)

## Executive Summary
| Component | Status | Notes |
|-----------|--------|-------|
| **Sentinel** | ✅ OK | State loaded, last check 1773829201 (recent) |
| **Quant** | ✅ OK | AlphaStrike active, signals current |
| **Shield** | ⚠️ MISSING | access-control.json not found at expected path |
| **Herald** | ✅ OK | State loaded, metrics empty (expected) |
| **EvoClaw Hub** | 🚨 DOWN | Service not running, no agents registered |
| **AlphaStrike** | ✅ ACTIVE | systemd service active, processing candles |
| **Alex Eye (Pi)** | 🚨 DOWN | SSH connection refused to 10.0.0.50 |

---

## Detailed Findings

### 1. Sentinel (workspace-sentinel)
- **State file:** ✅ Loaded
- **Last checks:**
  - Prices: 1773829201 (Sat Mar 15 03:00:01 2026 - recent)
  - Polymarket: 0 (never run)
  - Health: 0 (never run)
- **Recent alerts (24h):**
  - Fear & Greed (extreme fear): 2026-03-13
  - BTC thresholds: 70000, 75000
  - HYPE thresholds: 30, 25
  - SOL 3% decline
- **Open alerts:** None requiring immediate action

### 2. Quant (workspace-quant)
- **State file:** ✅ Loaded
- **Status:** ACTIVE, v4, recommissioned 2026-03-10
- **Strategy:** HL perps via AlphaStrike
- **Account value:** $112.22
- **Open positions:** None
- **Signals (2026-03-14 11:19:18 UTC):**
  - BTC: HOLD (no signal)
  - ETH: LONG @ 2069.45 (confidence 0.40 - below threshold)
  - SOL: LONG @ 86.67 (confidence 0.40 - below threshold)
- **AlphaStrike service:** ✅ Active
  - Processing: BTC (376 candles), ETH (291), SOL (305)
  - Last candles: BTC 70480, ETH 2073.6, SOL 86.77

### 3. Shield (access-control)
- **State file:** ❌ NOT FOUND
  - Expected: `/home/bowen/.openclaw/memory/access-control.json`
  - **Action required:** Initialize or restore access control state

### 4. Herald (workspace-herald)
- **State file:** ✅ Loaded
- **Metrics:** Empty (expected - no recent campaigns)
- **Scheduled posts:** None
- **Last checks:** All zero (inactive)

### 5. EvoClaw Hub (localhost:8420)
- **API endpoint:** 🚨 DOWN (connection failed)
- **Systemd service:** NOT FOUND
- **Running processes:** None
- **Action required:** Install and start evo-claw-hub service

### 6. Alex Eye (Pi 10.0.0.50)
- **SSH status:** 🚨 DOWN (Connection refused)
- **Action required:** Check Pi power/network, restart sshd if needed

---

## Actions Required

### Critical (DOWN)
1. **EvoClaw Hub:** Service not installed or not running
   - Check install: `which evo-claw-hub`
   - Check logs: `journalctl --user -u evo-claw-hub`
   - Restart if installed: `systemctl --user start evo-claw-hub`

2. **Alex Eye (Pi):** SSH connection refused
   - Verify Pi is powered on
   - Check network connectivity to 10.0.0.50
   - Restart sshd on Pi if needed

### Warning
3. **Shield:** State file missing
   - Verify correct path or reinitialize access control

---

## Automated Alert Status
**No alerts sent** — only DOWN components trigger alerts, and manual intervention required for both (Hub install, Pi hardware/network).
