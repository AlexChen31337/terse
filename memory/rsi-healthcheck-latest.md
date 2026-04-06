# RSI Health Check — 2026-04-06 03:11 AEDT

## Status
- **Health Score: 0.296** ⚠️ (below 0.3 threshold)
- **Outcomes (7d):** 9 logged | Success: 56% | Avg quality: 2.67/5
- **Patterns:** 3 detected | Analyzed: 2026-04-05
- **Proposals:** 1 draft | 0 approved | 24 deployed

## Top Issues
1. **context_loss** (5 occurrences) — session_management tasks, 0% failure rate (recovered but recurrent)
2. **incomplete_task** (2 occurrences) — message_routing tasks, 100% failure rate
3. **tool_validation_error** (1 occurrence) — tool_call tasks, 100% failure rate

## Pattern Details
| Confidence | Domain | Pattern | Count | Fail Rate |
|------------|--------|---------|-------|-----------|
| 0.889 | message_routing | incomplete_task | 2 | 100% |
| 0.556 | session_management | context_loss | 5 | 0% |
| 0.444 | tool_call | tool_validation_error | 1 | 100% |

## Cycle Results
- Proposals generated: 3
- Auto-deployed: 0 (all already deployed)
- Awaiting review: 1
- Auto-fix: `[15c31c37] Address 'tool_validation_error' in 'tool_call' tasks`

## Action Required
- Health score < 0.3 — **Bowen notified**
- Main concern: context_loss is the most frequent issue (5x in 7 days)
- incomplete_task in message_routing has 100% fail rate (2x) — needs investigation
