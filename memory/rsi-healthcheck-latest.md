# RSI Loop Health Check Report
**Date:** 2026-03-19 (3:00 AM AEDT)
**Run ID:** cron:8cc932c5-64f8-4a10-9ed7-0beef8c63ba2

## Status Summary
- **Health Score:** 0.135 / 1.0 ⚠️ (below 0.3 threshold)
- **Tests:** 32 passed ✅
- **Outcomes (7d):** 150 logged
- **Success Rate:** 31%
- **Avg Quality:** 2.15/5

## Critical Patterns Detected
1. **[0.980] tool_error in tool_call tasks** — 49 occurrences, 100% failure rate
2. **[0.620] timeout in tool_call tasks** — 31 occurrences, 100% failure rate
3. **[0.613] context_loss in session_management tasks** — 46 occurrences, 0% failure rate
4. **[0.520] tool_validation_error in tool_call tasks** — 18 occurrences, 100% failure rate
5. **[0.510] context_loss in tool_call tasks** — 9 occurrences, 0% failure rate

## Proposals Status
- **Generated:** 5 proposals (all already deployed)
- **Deployed:** 24 total proposals in history
- **Awaiting Review:** 0

## Test Results
```
32 passed in 1.04s
```
All tests passing:
- test_auto_observe.py: 20/20 ✅
- test_auto_fix.py: 12/12 ✅

## Alert Condition
**⚠️ Health score (0.135) is below 0.3 threshold**

The RSI Loop is detecting systemic issues:
- High failure rate in tool_call tasks (49 tool_errors, 31 timeouts)
- Significant context loss events (46 in session_management, 9 in tool_call)
- All proposals for these patterns have already been deployed but issues persist

**Recommendation:** Bowen should review the deployed fixes and consider:
1. Why tool_call tasks are failing at 100% rate
2. Whether the deployed proposals are effective
3. If deeper architectural changes are needed beyond auto-fix proposals
