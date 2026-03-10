# Nightly Health Check
**Date:** 2026-03-11 00:05 AEDT (2026-03-10 13:05 UTC)

## Results

| Service | Status | Details |
|---------|--------|---------|
| **AlphaStrike** | ✅ Active | Running |
| **EvoClaw Hub** | ❌ DOWN | API not responding |
| **GPU Server** | ✅ Online | All 3 GPUs responsive |
| **Skills** | ✅ 56 | Installed |
| **Memory Files** | ✅ 156 | Daily notes |

## GPU Status (peter@10.0.0.44)
- **GPU 0:** RTX 3090 — 19998 MiB / 24576 MiB (81% used)
- **GPU 1:** RTX 3080 — 18 MiB / 10240 MiB (0.2% used)
- **GPU 2:** RTX 2070 SUPER — 9 MiB / 8192 MiB (0.1% used)

## Action Required
- **EvoClaw hub is DOWN** — investigate `http://localhost:8420/api/agents`
- Check if `evoclaw-hub` service is running: `systemctl --user status evoclaw-hub`
- Review logs: `journalctl --user -u evoclaw-hub -n 50`