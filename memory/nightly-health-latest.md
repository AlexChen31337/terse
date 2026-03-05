# Nightly Health Check Report
**Date:** 2026-03-06 12:05 AM AEDT

## Services
| Service | Status |
|---------|--------|
| AlphaStrike | ✅ active |
| EvoClaw hub | ❌ DOWN (API unreachable) |
| GPU server | ✅ online |

## GPU Server (10.0.0.44)
| GPU | VRAM Used | VRAM Total |
|-----|-----------|------------|
| RTX 3090 | 19.9 GB | 24 GB |
| RTX 3080 | 18 MB | 10 GB |
| RTX 2070 SUPER | 9 MB | 8 GB |

## Workspace
- Skills installed: 53
- Memory files: 145

## Alerts
- 🚨 **EvoClaw hub API is not responding** - service may be down
- Recommendation: `systemctl --user status evoclaw-hub`
