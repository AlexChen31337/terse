# RSI Loop Health Check Report
**Date:** 2026-03-21 03:00 AEDT (2026-03-20 16:00 UTC)
**Status:** ⚠️ HEALTH SCORE BELOW THRESHOLD (0.146 < 0.3)

---

## Summary

| Metric | Value |
|--------|-------|
| Health Score | **0.146** ⚠️ |
| Outcomes (7d) | 162 logged |
| Success Rate | 33% |
| Avg Quality | 2.2/5 |
| Patterns | 5 detected |
| Proposals | 5 generated (all already deployed) |

## Test Results
✅ All 32 tests passed (1.05s)

## Top Failure Patterns (Last 7 Days)

1. **[0.939] timeout in tool_call tasks** — 51 occurrences, 100% failure rate
2. **[0.681] tool_error in tool_call tasks** — 37 occurrences, 100% failure rate
3. **[0.650] context_loss in session_management tasks** — 53 occurrences, 0% failure rate
4. **[0.570] timeout in tool_call tasks** — 51 occurrences, 100% failure rate
5. **[0.539] context_loss in session_management tasks** — 53 occurrences, 0% failure rate

## Deployed Fixes

All 5 generated proposals have already been deployed:
- db32089a: Address 'timeout' in 'tool_call' tasks
- b9e26a71: Address 'tool_error' in 'tool_call' tasks
- 60126e7f: Address 'context_loss' in 'session_management' tasks
- 15c31c37: Address 'tool_validation_error' in 'tool_call' tasks
- 84a2e40b: Address 'context_loss' in 'session_management' tasks

## Alert Condition Triggered

Health score 0.146 is below the 0.3 threshold. Bowen has been notified.

---

**Next check:** 2026-03-22 03:00 AEDT
