# Nightly Health Check Report
**Date:** 2026-03-15 00:19 AEDT  
**Run ID:** ca76fb23-4d97-4061-88dd-91c24ca09c5e

## Results

| Service | Status | Details |
|---------|--------|---------|
| **AlphaStrike** | ✅ UP | `active` |
| **EvoClaw Hub** | ❌ DOWN | HTTP 8420 not responding |
| **GPU Server** | ✅ ONLINE | RTX 3090 (20GB/24GB), RTX 3080 (18MB/10GB), RTX 2070 SUPER (9MB/8GB) |
| **Skills** | ✅ 59 | Installed in workspace |
| **Memory Files** | ✅ 162 | Daily notes archived |

## Issues Detected

**🚨 EvoClaw Hub is DOWN**
- Local HTTP API on port 8420 is not responding
- This may indicate the gateway or agent runtime has stopped
- Manual intervention may be required

## Summary

- **Critical Issues:** 1 (EvoClaw Hub)
- **Healthy Systems:** 4 (AlphaStrike, GPU Server, Skills, Memory)

**Recommendation:** Check OpenClaw gateway status and restart if needed.
