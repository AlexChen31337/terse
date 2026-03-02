# Nightly Health Check Report
**Date:** 2026-03-03 00:05 AEDT
**Run by:** cron job (ca76fb23)

## Results

| Service | Status | Details |
|---------|--------|---------|
| **AlphaStrike** | ✅ Active | Running normally |
| **EvoClaw Hub** | ❌ DOWN | Not responding at localhost:8420 |
| **GPU Server** | ✅ Online | 3 GPUs: 3090 (20GB/24GB), 3080 (18MB/10GB), 2070S (9MB/8GB) |
| **Skills** | ✅ 44 | Installed |
| **Memory Files** | ✅ 138 | Daily notes available |

## Issues Found

1. **EvoClaw hub service is down** — The service at `http://localhost:8420/api/agents` is not responding. This may affect agent communication and MQTT functionality.

## Recommendation

Check EvoClaw hub status:
```bash
systemctl --user status evoclaw-hub.service
# or
journalctl --user -u evoclaw-hub -n 50
```

If the service is failing, investigate logs and restart if needed.
