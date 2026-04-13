# RSI Loop Health Check — 2026-04-13 03:10 AEDT

## Status
- **Health Score:** 0.2 ⚠️ (below 0.3 threshold)
- **7-Day Outcomes:** 21 logged
- **Success Rate:** 43%
- **Avg Quality:** 2.33/5

## Top Issues
| Issue | Count | Failure Rate |
|-------|-------|-------------|
| context_loss | 9 | — |
| tool_validation_error | 7 | 100% |
| incomplete_task | 4 | 100% (message_routing) |

## Patterns Detected (4)
1. **[1.333]** tool_validation_error in tool_call tasks — 7x, 100% fail
2. **[0.762]** incomplete_task in message_routing tasks — 4x, 100% fail
3. **[0.429]** context_loss in session_management tasks — 9x, 0% failure (context_loss isn't fatal)

## Cycle Results
- Proposals generated: 4
- Auto-deployed: 0 (all already deployed)
- Awaiting review: 1

## Action Taken
- Alerted Bowen via Telegram (health < 0.3)
