# RSI Weekly Report — 2026-04-19

**Cycle Date:** 2026-04-18 17:00 UTC
**Period:** 7 days

## Summary
| Metric | Value |
|--------|-------|
| Outcomes (7d) | 32 logged |
| Success Rate | 31% |
| Avg Quality | 2.28/5 |
| Health Score | **0.143** ⚠️ |
| Patterns Detected | 5 |
| Proposals Generated | 5 |
| Auto-Deployed | 0 |
| Awaiting Review | 1 |
| Total Deployed | 24 |

## Top Issues
1. **context_loss** — 10 occurrences
2. **tool_error** — 10 occurrences
3. **incomplete_task** — 8 occurrences

## Key Patterns
1. `[1.000]` In `message_routing` tasks, `incomplete_task` occurs 8x with 100% fail
2. `[0.938]` In `tool_call` tasks, `tool_error` occurs 10x with 100% failure rate
3. `[0.375]` In `tool_call` tasks, `tool_validation_error` occurs 3x with 100% fail

## Action Items
- 1 proposal awaiting manual review
- Health score critically low — primarily driven by tool failures and context loss in message routing
- All 5 auto-eligible proposals were already deployed (skipped as duplicates)
