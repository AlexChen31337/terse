# Midnight Health Report
**Generated:** 2026-03-13 00:00 AEDT (2026-03-12 13:00 UTC)
**Cron Job:** 3b4465c3-4a20-4e25-8325-30d108cd3f04

## Component Status

| Component | Status | Details |
|-----------|--------|---------|
| **Sentinel** | ✅ OK | State loaded, last price check: 2026-03-12 11:58 AM UTC |
| **Quant** | ✅ OK | State loaded, AlphaStrike service: ACTIVE (systemd) |
| **Shield** | ⚠️ NOT FOUND | access-control.json does not exist |
| **Herald** | ✅ OK | State loaded, no scheduled posts pending |
| **EvoClaw Hub** | ✅ OK | 2 agents registered |
| **Alex Eye (Pi)** | ❌ DOWN | SSH timeout, ping failed |

## Sentinel Details
- **Last Prices:** BTC $70,359.50 | ETH $2,063.55 | SOL $87.10 | HYPE $37.47
- **Fear & Greed:** 18 (Extreme Fear)
- **Last Alerts (24h):** 7 alerts logged (BTC/HYPE thresholds)

## Quant Details
- **Account Value:** $112.22
- **Open Positions:** None
- **Signals:** LONG BTC/ETH/SOL (all confidence 0.40 — no trades triggered)
- **Consecutive Losses:** 0
- **Circuit Breakers:** Armed (daily target 5%, stop -3%)

## Shield Status
- access-control.json not found at `/home/bowen/.openclaw/access-control.json`
- This may need initialization or path verification

## Herald Details
- No active scheduled posts
- No recent outreach activity

## EvoClaw Hub
- 2 agents registered
- Responding on http://localhost:8420/api/agents

## Alex Eye (Pi) — ❌ DOWN
- **SSH:** Connection timeout
- **Ping:** Failed (host unreachable)
- **IP:** 10.0.0.100
- **Action Required:** Manual intervention — Pi may be offline or network issue

## Summary
- **5/6 components OK**
- **1 DOWN:** Alex Eye (Pi) — requires manual restart or network troubleshooting
