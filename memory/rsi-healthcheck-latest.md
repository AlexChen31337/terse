# RSI Loop Health Check — 2026-04-10 03:20 AEST

## ⚠️ HEALTH SCORE: 0.286 (BELOW THRESHOLD 0.3)

## Summary
- **Outcomes (7d):** 26 logged | Success rate: 54% | Avg quality: 2.65/5
- **Patterns detected:** 4
- **Proposals:** 1 draft | 0 approved | 24 deployed

## Top Issues
| Issue | Count | Context |
|---|---|---|
| `context_loss` | 14 | session_management tasks |
| `tool_validation_error` | 6 | tool_call tasks (100% fail) |
| `incomplete_task` | 5 | message_routing tasks (100% fail) |

## Pattern Details
1. **[0.923]** `tool_validation_error` in `tool_call` tasks — 6x, 100% failure
2. **[0.769]** `incomplete_task` in `message_routing` tasks — 5x, 100% failure
3. **[0.538]** `context_loss` in `session_management` tasks — 14x

## Cycle Results
- Ran full RSI cycle with auto-approval
- 4 proposals generated, 0 newly deployed (3 already deployed)
- 1 proposal awaiting review: `3b8e8f52` — Address `incomplete_task` in `message_routing` (critical, draft)

## Actionable Items
1. **Review proposal `3b8e8f52`** — critical priority, addresses message_routing incomplete_task pattern (52 duplicate detections)
2. **context_loss (14x)** is the biggest volume issue — existing deployment `60126e7f` may not be fully effective
3. **tool_validation_error (6x, 100% fail)** — existing deployment `15c31c37` needs effectiveness review

## Alert Trigger
Health score 0.286 < 0.3 threshold → Bowen alerted via message.
