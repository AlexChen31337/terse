# RSI Weekly Report — 2026-04-26

**Cycle Date:** 2026-04-25 17:00 UTC
**Period:** 7 days
**Health Score:** 0.22 ⚠️ (threshold: 0.3)

## Outcomes (7d)
- **Total:** 64 logged
- **Success rate:** 41%
- **Avg quality:** 2.7/5
- **Top issues:** tool_error (29), context_loss (26), tool_validation_error (5)

## Patterns Detected (4)
1. **[1.359]** In `tool_call` tasks, `tool_error` occurs 29x with 100% failure rate
2. **[0.406]** In `session_management` tasks, `context_loss` occurs 26x with 0% failure rate
3. **[0.312]** In `tool_call` tasks, `tool_validation_error` occurs 5x with 100% failure rate
4. (4th pattern — lower significance)

## Proposals
- **Generated:** 4 (all already deployed or auto-approved)
- **Draft:** 0
- **Awaiting review:** 0
- **Deployed total:** 24

## Assessment
Health score below 0.3 threshold. Primary concern is the high `tool_error` rate in tool_call tasks (29 occurrences, 100% failure). Context loss in session management is frequent but non-failing. The deployed proposals haven't moved the needle yet — may need fresh analysis.

## Action
Alert sent to Bowen via Telegram.
