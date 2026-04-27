# RSI Loop Health Check — 2026-04-27 03:10 AEST

## Status
- **Health Score: 0.216** ⚠️ (threshold: 0.3)
- **Outcomes (7d):** 72 logged
- **Success Rate:** 40%
- **Avg Quality:** 2.68/5

## Top Issues
1. **tool_error** — 32 occurrences (100% failure rate in tool_call tasks)
2. **context_loss** — 29 occurrences (0% failure rate in session_management)
3. **tool_validation_error** — 7 occurrences (100% failure rate in tool_call tasks)

## Patterns Detected: 4
1. `[1.315]` In 'tool_call' tasks, 'tool_error' occurs 32x with 100% failure rate
2. `[0.397]` In 'session_management' tasks, 'context_loss' occurs 29x with 0% failure
3. `[0.384]` In 'tool_call' tasks, 'tool_validation_error' occurs 7x with 100% failure

## Cycle Results
- Proposals generated: 4
- Auto-deployed: 0 (all already deployed or auto-approved)
- Awaiting review: 0

## Proposals (already deployed)
- `b9e26a71` — Address 'tool_error' in 'tool_call' tasks
- `15c31c37` — Address 'tool_validation_error' in 'tool_call' tasks

## Alert
⚠️ Health score below 0.3 — Telegram alert sent to Bowen.
