# RSI Loop Health Check Report
**Date:** 2026-03-25 03:00 AEDT
**Trigger:** Cron nightly health check

## System Status
- **Health Score:** 0.133 / 1.0 ⚠️
- **Outcomes (7d):** 225 logged
- **Success Rate:** 31%
- **Average Quality:** 2.13/5

## Top Failure Patterns (Last 7 Days)
1. **context_loss** (70 occurrences) - 31.1%
2. **timeout** (60 occurrences) - 26.7%
3. **tool_error** (55 occurrences) - 24.4%
4. **tool_validation_error** (37 occurrences) - 16.4%

## Detected Patterns
- [0.800] In 'tool_call' tasks, 'timeout' occurs 60x with 100% failure rate
- [0.733] In 'tool_call' tasks, 'tool_error' occurs 55x with 100% failure rate
- [0.658] In 'tool_call' tasks, 'tool_validation_error' occurs 37x with 100% failure rate

## Proposals Status
- Draft: 0
- Approved: 0
- Deployed: 24 (all current proposals already deployed)

## Auto-Fix Attempts
This cycle generated 5 proposals, all already deployed:
- db32089a: Address 'timeout' in 'tool_call' tasks
- b9e26a71: Address 'tool_error' in 'tool_call' tasks
- 15c31c37: Address 'tool_validation_error' in 'tool_call' tasks

## Test Results
✅ **All 32 tests passed** (4.09s)
- test_auto_observe.py: 20/20 passed
- test_auto_fix.py: 12/12 passed

## Analysis
**Critical Issue:** Health score (0.133) is significantly below the 0.3 threshold. The system is experiencing high failure rates in tool_call tasks, with timeouts and tool errors being the dominant failure modes.

**Root Cause:** The patterns suggest infrastructure or API reliability issues affecting tool execution, particularly around timeouts and validation errors.

**Recommendation:** Review tool execution infrastructure, timeout configurations, and API reliability. Consider implementing circuit breakers or retry logic for failing tool calls.

## Next Steps
1. Investigate root cause of tool_call timeouts
2. Review and increase timeout thresholds if appropriate
3. Implement better error recovery for tool_validation_error
4. Consider adding monitoring/alerting for health score drops
