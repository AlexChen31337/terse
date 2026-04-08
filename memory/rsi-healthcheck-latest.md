# RSI Loop Health Check — 2026-04-08 03:15 AEDT

## Status
- **Health Score: 0.159** ⚠️ (threshold: 0.3)
- **Outcomes (7d):** 19 logged | Success: 37% | Avg quality: 2.16/5
- **Top Issues:** context_loss(7), tool_validation_error(6), incomplete_task(4)
- **Patterns Detected:** 4
- **Proposals:** 1 draft | 0 approved | 24 deployed

## Key Patterns
1. **tool_validation_error** in `tool_call` tasks — 6x, 100% fail rate (score: 1.263)
2. **incomplete_task** in `message_routing` tasks — 4x, 100% fail rate (score: 0.842)
3. **context_loss** in `session_management` tasks — 7x (score: 0.368)

## Cycle Results
- Proposals generated: 4 (all already deployed or auto-skipped)
- Auto-deployed: 0
- Awaiting review: 1

## Action Required
- Health score critically low at 0.159
- Main driver: persistent tool_validation_error and incomplete_task failures
- Existing proposals may not be addressing root cause sufficiently
