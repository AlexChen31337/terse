# RSI Loop Health Check — 2026-04-19 03:11 AEST

## Status
- **Health Score: 0.143** ⚠️ (threshold: 0.3)
- **Outcomes (7d):** 32 logged
- **Success Rate:** 31%
- **Avg Quality:** 2.28/5

## Top Issues
| Issue | Count |
|-------|-------|
| context_loss | 10 |
| tool_error | 10 |
| incomplete_task | 8 |

## Detected Patterns
1. **[1.000]** `message_routing` tasks → `incomplete_task` (8x, 100% fail)
2. **[0.938]** `tool_call` tasks → `tool_error` (10x, 100% failure rate)
3. **[0.375]** `tool_call` tasks → `tool_validation_error` (3x, 100% fail)

## Cycle Results
- Proposals generated: 5
- Auto-deployed: 0
- Awaiting review: 1
- Already deployed (skipped): 4

## Pending Proposals
- `b9e26a71`: Address `tool_error` in `tool_call` tasks (already deployed)
- `15c31c37`: Address `tool_validation_error` in `tool_call` tasks (already deployed)
- `60126e7f`: (already deployed)
- `db32089a`: Address `timeout` in `tool_call` tasks (already deployed)

## Action Taken
- ⚠️ Alerting Bowen via Telegram (health score < 0.3)
