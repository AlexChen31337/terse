# RSI Loop Health Check — 2026-04-22 03:14 AEDT

## Status
- **Health Score: 0.18** ⚠️ (threshold: 0.3)
- **Outcomes (7d):** 48 logged | Success: 35% | Avg quality: 2.52/5

## Top Issues
| Issue | Count | Context |
|-------|-------|---------|
| tool_error | 22 | tool_call tasks |
| context_loss | 17 | session_management tasks |
| incomplete_task | 6 | message_routing tasks |

## Patterns Detected (4)
1. **[1.403]** `tool_call` → `tool_error` at 100% failure rate (29 occurrences)
2. **[0.516]** `message_routing` → `incomplete_task` at 100% fail (8 occurrences)
3. **[0.355]** `session_management` → `context_loss` at 0% failure (22 occurrences)

## Cycle Results
- Proposals generated: 4 (all already deployed)
- Auto-deployed: 0
- Awaiting review: 0
- One approved proposal ready: `3b8e8f52` (address incomplete_task in message_routing)

## Action Taken
- ⚠️ **Bowen alerted via Telegram** — health score below threshold
- Cycle completed, no new proposals to deploy
- Recommendation: investigate recurring tool_error pattern (22 instances, 100% failure)
