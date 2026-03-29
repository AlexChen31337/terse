# Nightly Health Check — 2026-03-30 00:06 AEDT

| Component     | Status                                         |
|---------------|------------------------------------------------|
| AlphaStrike   | ✅ active                                      |
| EvoClaw Hub   | 🔴 DOWN (no response on :8420)                 |
| GPU Server    | ✅ online — RTX 3090: 38/24576 MiB · RTX 3080: 15/10240 MiB · RTX 2070 SUPER: 6/8192 MiB |
| ClawMemory    | ✅ v0.1.0 · facts=20                           |
| Skills count  | 74                                             |
| Memory files  | 192                                            |

## Summary
- ⚠️ **EvoClaw Hub DOWN** — `curl http://localhost:8420/api/agents` returned no response. EvoClaw hub process may have crashed or not started.
- All other services nominal.
- GPU server idle (minimal VRAM usage across all 3 GPUs).
