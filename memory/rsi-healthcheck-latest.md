# RSI Loop Health Check Report
**Date:** 2026-04-12 03:10 AEDT (2026-04-11 17:10 UTC)

## Status
- **Health Score:** 0.274 ⚠️ (below 0.3 threshold)
- **7-Day Outcomes:** 21 logged
- **Success Rate:** 52%
- **Avg Quality:** 2.62/5

## Top Issues
| Issue | Count | Fail Rate |
|-------|-------|-----------|
| context_loss | 11 | 0% |
| tool_validation_error | 6 | 100% |
| incomplete_task | 3 | 100% |

## Patterns Detected (4)
1. **[1.143]** In `tool_call` tasks, `tool_validation_error` occurs 6x with 100% fail
2. **[0.571]** In `message_routing` tasks, `incomplete_task` occurs 3x with 100% fail
3. **[0.524]** In `session_management` tasks, `context_loss` occurs 11x with 0% failure

## Cycle Result
- Proposals generated: 4
- Auto-deployed: 0 (all already deployed)
- Awaiting review: 1
- Deployed to date: 24

## Pending Proposals
- `15c31c37` — Address `tool_validation_error` in `tool_call` tasks (already deployed)
- `db32089a` — Address `timeout` in `tool_call` tasks (already deployed)

## Alert
Telegram alert sent to Bowen (health score < 0.3).
