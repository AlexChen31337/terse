# RSI Loop Health Check — 2026-04-21 03:14 AEST

## Status
- **Health Score:** 0.18 ⚠️ (threshold: 0.3 — ALERT sent to Bowen)
- **7-Day Outcomes:** 62 logged | Success: 36% | Avg quality: 2.53/5

## Top Issues
| Issue | Count | Failure Rate |
|-------|-------|-------------|
| tool_error | 29 | 100% (in tool_call tasks) |
| context_loss | 22 | 0% failure (session_management) |
| incomplete_task | 8 | 100% (message_routing) |

## Patterns Detected (4)
1. **[lift 1.403]** tool_call tasks → tool_error (29x, 100% fail)
2. **[lift 0.516]** message_routing → incomplete_task (8x, 100% fail)
3. **[lift 0.355]** session_management → context_loss (22x)

## Proposals
- 1 draft awaiting review
- 24 already deployed
- Auto-cycle deployed 0 new (all proposals already deployed)

## Action Taken
- Alert sent to Bowen via Telegram (health score < 0.3)
- Recommend investigating tool_error pattern in tool_call tasks
