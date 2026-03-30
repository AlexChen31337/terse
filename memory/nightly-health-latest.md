# Nightly Health Check
**Date:** 2026-03-31 00:06 AEDT (2026-03-30 13:06 UTC)

## Results

| Component       | Status         | Detail                          |
|-----------------|----------------|---------------------------------|
| AlphaStrike     | 🔴 DOWN        | service state: activating/DOWN  |
| EvoClaw Hub     | 🔴 DOWN        | http://localhost:8420 unreachable |
| GPU Server      | 🔴 offline     | ssh peter@10.0.0.44 timed out   |
| ClawMemory      | 🟢 OK          | v0.1.0, facts=313               |
| Skills Count    | 🟢 74          | ~/.openclaw/workspace/skills/   |
| Memory Files    | 🟢 194         | ~/.openclaw/workspace/memory/   |

## Summary
- **3 issues detected:** AlphaStrike DOWN, EvoClaw Hub DOWN, GPU Server offline
- ClawMemory healthy with 313 active facts
- Workspace: 74 skills, 194 memory files

## Actions Taken
- Alert sent to Bowen via Telegram
