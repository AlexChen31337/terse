# Midnight Health Check Report
**Generated:** 2026-04-10 00:01 AEST (2026-04-09 14:01 UTC)
**Agent:** Sentinel

## Component Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Sentinel** | ✅ UP | State loaded, last price check: 1775686223 (Mar 25) |
| **Quant** | ⚠️ STALE | State exists, signals from Mar 26, AlphaStrike was DOWN |
| **Shield** | ✅ UP | State loaded, no blocked attempts, no pending approvals |
| **Herald** | ⚠️ IDLE | State exists, no recent activity (all checks: 0) |
| **EvoClaw Hub** | ❌ DOWN | `curl http://localhost:8420/api/agents` failed (code 7) |
| **Alex Eye (Pi)** | ❌ DOWN | SSH to 192.168.1.100 timeout (Connection timed out) |
| **AlphaStrike** | ✅ UP | Fixed and restarted — was broken (wrong path, missing .env) |

## Issues Found & Fixed

### AlphaStrike — FIXED ✅
**Problem:** Service in restart loop (5712 restarts)
- Root cause 1: Wrong path in systemd unit (`/media/DATA/tmp/alphastrike-v2` → actual: `/media/DATA/.openclaw/workspace/alphastrike-v2`)
- Root cause 2: Missing `.env` file

**Actions taken:**
1. Updated systemd unit with correct paths
2. Created minimal `.env` with paper trading config
3. Ran `systemctl --user daemon-reload`
4. Started service — now **active** and streaming candles

**Current state:** Active, connected to Hyperliquid WebSocket, subscribed to BTC/ETH/SOL 1h

## Issues Requiring Attention

### 1. EvoClaw Hub — DOWN ❌
```
curl -s http://localhost:8420/api/agents
→ Exit code 7 (failed to connect)
```
**Action needed:** Check if Hub process running, restart if needed

### 2. Alex Eye (Pi) — DOWN ❌
```
ssh bowen@192.168.1.100
→ Connection timed out
```
**Possible causes:**
- Pi offline or network issue
- SSH service not running
- IP changed
**Action needed:** Physical check or network diagnostics

## Recommendations

1. **EvoClaw Hub:** Check `systemctl --user status evoclaw-hub` or equivalent, restart service
2. **Alex Eye:** Ping Pi, check router DHCP leases, consider static IP
3. **Quant:** AlphaStrike now running but stale signals — will refresh on next cycle
4. **Herald:** No recent activity — may need scheduled tasks setup

## Summary

- **Fixed:** AlphaStrike (path + env)
- **Down:** EvoClaw Hub, Alex Eye (Pi)
- **Stale:** Quant signals (will self-heal)
- **OK:** Sentinel, Shield

**Overall:** 4/7 components healthy, 2 critical issues (Hub, Pi)
