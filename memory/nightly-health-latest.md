# Nightly Health Check Report
**Date:** 2026-03-05 12:05 AM AEDT
**Trigger:** Nightly cron

## Results

| Service | Status | Details |
|---------|--------|---------|
| **AlphaStrike** | ✅ ACTIVE | Running normally |
| **EvoClaw Hub** | ❌ DOWN | API unreachable on http://localhost:8420 |
| **GPU Server** | ✅ ONLINE | All 3 GPUs responsive |
| **Skills** | ✅ 45 | Installed skill count |
| **Memory Files** | ✅ 145 | Daily notes stored |

## GPU Status (peter@10.0.0.44)
- RTX 3090: 19966 MiB / 24576 MiB (81% used)
- RTX 3080: 18 MiB / 10240 MiB (idle)
- RTX 2070 SUPER: 9 MiB / 8192 MiB (idle)

## Alert Required
⚠️ **EvoClaw hub is DOWN** - Alerting Bowen via Telegram
