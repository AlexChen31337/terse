# Midnight Health Check Report
**Generated:** 2026-03-26 00:00 AEDT (2026-03-25 13:00 UTC)

## Component Status

| Component | Status | Details |
|-----------|--------|---------|
| **Sentinel** | ✅ HEALTHY | Last check: 2026-03-25 12:47 UTC (prices, F&G) |
| **Quant** | ⚠️ STALE | Signals from 2026-03-25; AlphaStrike service UP |
| **Shield** | ❓ NOT FOUND | access-control.json missing |
| **Herald** | ⚠️ INACTIVE | No checks run recently (Twitter/Moltbook: 0) |
| **EvoClaw Hub** | ✅ UP | 2 agents registered |
| **Alex Eye (Pi)** | ❌ DOWN | SSH connection refused |

---

## Detailed Findings

### Sentinel ✅
- State file: Current
- Last price check: 2026-03-25 12:47:54 UTC
- Last Fear & Greed: Extreme Fear (14)
- Alerts in last 24h: Multiple (BTC price thresholds, HYPE thresholds, FNG category)
- **Verdict:** Healthy and monitoring

### Quant ⚠️
- State file: Present but stale (signals ~12h old)
- AlphaStrike service: ✅ Active (systemd)
- Open positions: None
- Account value: $112.22
- **Verdict:** Service running but data stale; may need refresh

### Shield ❓
- access-control.json: **NOT FOUND**
- Cannot verify access control status
- **Verdict:** Needs investigation/initialization

### Herald ⚠️
- State file: Present but inactive
- Last checks: Twitter (0), Moltbook (0), Analytics (0)
- No posts or outreach activity logged
- **Verdict:** Not running; needs activation

### EvoClaw Hub ✅
- Endpoint: http://localhost:8420/api/agents
- Status: Responding
- Registered agents: 2
- **Verdict:** Healthy

### Alex Eye (Pi) ❌
- Host: pi@10.0.0.50
- Status: SSH connection refused
- **Action taken:** Restart attempted
- **Verdict:** DOWN despite restart attempt

---

## Alerts Required
- **Alex Eye (Pi):** ❌ DOWN — Restart failed, manual intervention needed
