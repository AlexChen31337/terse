# RSI Loop Health Check — 2026-04-11 03:10 AEDT

## Status Summary
- **Health Score: 0.286** ⚠️ BELOW THRESHOLD (< 0.3)
- **7-day outcomes:** 26 logged
- **Success rate:** 54%
- **Avg quality:** 2.65/5

## Top Issues
| Issue | Count | Fail Rate |
|-------|-------|-----------|
| context_loss | 14 | 0% fail (recoverable) |
| tool_validation_error | 6 | 100% fail |
| incomplete_task | 5 | 100% fail |

## Patterns Detected (4)
1. **[0.923]** `tool_call` tasks → `tool_validation_error` 6x, 100% fail
2. **[0.769]** `message_routing` tasks → `incomplete_task` 5x, 100% fail
3. **[0.538]** `session_management` tasks → `context_loss` 14x, 0% failure

## Proposals
- **Draft:** 1
- **Approved:** 0
- **Deployed:** 24
- **Auto-deployed this cycle:** 0 (all existing proposals already deployed)

## Cycle Actions
- 4 proposals generated, 0 new auto-deployed
- 2 proposals noted as already addressing top issues

## Alert
⚠️ Health score 0.286 is below 0.3 threshold — Bowen notified.
