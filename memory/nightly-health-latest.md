# Nightly Health Check Report
**Date:** 2026-03-07 12:05 AM AEDT
**Status:** 🚨 ISSUE DETECTED

## Results

| Service | Status | Details |
|---------|--------|---------|
| **AlphaStrike** | ✅ active | systemd user service running |
| **EvoClaw hub** | ❌ DOWN | API not responding on localhost:8420 |
| **GPU server** | ✅ online | 3 GPUs detected |
| **Skills** | ✅ 53 | OpenClaw workspace skills |
| **Memory files** | ✅ 146 | Daily notes stored |

## GPU Details (peter@10.0.0.44)
- RTX 3090: 19966 MiB / 24576 MiB (81% used)
- RTX 3080: 18 MiB / 10240 MiB (0% used)
- RTX 2070 SUPER: 9 MiB / 8192 MiB (0% used)

## Action Required
EvoClaw hub is not responding. Check:
```bash
journalctl --user -u alphastrike.service -n 50
```

---
*Report saved to memory/nightly-health-latest.md*