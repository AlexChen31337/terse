# RSI Loop Health Check — 2026-04-18 03:10 AEST

## Status
- **Health Score:** 0.136 (⚠️ CRITICAL — below 0.3 threshold)
- **Outcomes (7d):** 30 logged
- **Success Rate:** 30%
- **Avg Quality:** 2.27/5

## Top Issues
| Issue | Count |
|-------|-------|
| tool_error | 10 |
| context_loss | 9 |
| incomplete_task | 8 |

## Detected Patterns
1. **[1.077]** `message_routing` tasks → `incomplete_task` 7x, 100% fail
2. **[0.923]** `tool_call` tasks → `tool_error` 8x, 100% failure
3. **[0.308]** `tool_call` tasks → `tool_validation_error` 2x, 100% fail

## Cycle Results
- **Proposals generated:** 5
- **Auto-deployed:** 0 (all already deployed)
- **Awaiting review:** 1

## Action
- Alert sent to Bowen via Telegram (health < 0.3)
- Existing proposals already deployed; new proposal awaiting manual review
