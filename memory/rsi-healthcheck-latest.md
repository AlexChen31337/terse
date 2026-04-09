# RSI Loop Health Check — 2026-04-09 03:10 AEDT

## Status
- **Health Score: 0.173** ⚠️ (threshold: 0.3)
- **Outcomes (7d):** 18 logged | Success: 39% | Avg quality: 2.22/5
- **Top Issues:** context_loss(7), tool_validation_error(6), incomplete_task(4)

## Detected Patterns (4)
1. **[1.333]** In `tool_call` tasks, `tool_validation_error` occurs 6x with 100% fail
2. **[0.889]** In `message_routing` tasks, `incomplete_task` occurs 4x with 100% fail
3. **[0.389]** In `session_management` tasks, `context_loss` occurs 7x with 0% failure rate

## Cycle Results
- Proposals generated: 4
- Auto-deployed: 0 (all already deployed)
- Awaiting review: 1
- Existing deployed: 24

## Pending Auto-Fixes
- `15c31c37`: Address `tool_validation_error` in `tool_call` tasks
- `db32089a`: Address `timeout` in `tool_call` tasks

## Action Required
Health score critically low. 39% success rate over 7 days. Main drivers are context loss and tool validation errors. Bowen alerted.
