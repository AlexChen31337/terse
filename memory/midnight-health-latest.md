# Midnight Health Check
**Generated:** 2026-03-28 00:00:17 AEDT (1774616417)

## Component Status

| Component | Status | Notes |
|---|---|---|
| **Sentinel** | ✅ OK | Last check: 2026-03-28 00:00 (1774614675, <1h ago). Prices tracking, Fear & Greed: Extreme Fear (13). |
| **Quant** | ⚠️ STALE | Last check: 2005-01-22 (1742915310). **Over 1 year stale.** Signals outdated. AlphaStrike service: ✅ active (logging recent candles). |
| **Shield** | 🔴 MISSING | access-control.json not found. Needs init. |
| **Herald** | ⚠️ IDLE | State exists but all metrics/lastChecks = 0. No recent activity. |
| **EvoClaw Hub** | ✅ OK | Running, 2 agents registered. |
| **Alex Eye (Pi)** | 🔴 DOWN | SSH unreachable. Restart attempted — **failed**. |

## Alertable Issues

1. **🔴 CRITICAL: Alex Eye (Pi) — DOWN**
   - SSH to 10.0.0.5 failed
   - Remote restart failed (PI_RESTART_FAILED)
   - **Action required:** Manual Pi intervention needed

2. **⚠️ WARNING: Quant state stale**
   - State file last updated: 2005-01-22
   - AlphaStrike service running but not updating state
   - Signals: BTC LONG @ 71214.5, ETH LONG @ 2163.15, SOL LONG @ 91.72 ( outdated)

3. **🔴 MISSING: Shield workspace**
   - access-control.json does not exist
   - Shield not initialized

4. **⚠️ IDLE: Herald**
   - No recent checks or posts
   - May need scheduling or manual trigger

## Sentinel Market State (current)
- BTC: $66,474.5
- ETH: $1,984.65
- SOL: $83.06
- HYPE: $38.04
- Fear & Greed: Extreme Fear (13)

## AlphaStrike Service (systemd)
- Status: **active**
- Recent logs: Buffering candles normally (BTC 494, ETH 344, SOL 351)

## Recommendations
1. **Immediate:** Manual check of Alex Eye Pi (power/network)
2. **High:** Fix Quant state update pipeline (service running but not persisting)
3. **Medium:** Initialize Shield workspace
4. **Low:** Review Herald scheduling
