# RSI Loop Health Check Report
**Date:** 2026-03-14 (3:00 AM AEDT / 2026-03-13 16:00 UTC)

## Health Score
**0.136 / 1.0** ⚠️ Low

## Status Summary
- **Outcomes (7d):** 142 logged
- **Success rate:** 31%
- **Average quality:** 2.19/5

## Top Failure Patterns
1. **[1.394]** tool_call → tool_error (66 occurrences, 100% failure)
2. **[0.620]** session_management → context_loss (44 occurrences, 0% failure)
3. **[0.451]** tool_call → tool_validation_error (16 occurrences, 100% failure)

## Proposals Status
- **Draft:** 0
- **Approved:** 0
- **Deployed:** 24

## Auto-Fix Proposals (Already Deployed)
- [b9e26a71] Address 'tool_error' in 'tool_call' tasks
- [15c31c37] Address 'tool_validation_error' in 'tool_call' tasks
- [db32089a] Address 'timeout' in 'tool_call' tasks
- [60126e7f] Address 'context_loss' in 'session_management' tasks

## Test Results
✅ All 32 tests passed (test_auto_observe.py + test_auto_fix.py)

## Analysis
The health score remains low (0.136) primarily due to persistent tool_call errors. However, all patterns have been analyzed and proposals have already been deployed. The RSI loop is functioning correctly — it's detecting issues, generating proposals, and deploying fixes.

The high occurrence of tool_error and tool_validation_error suggests tool configuration or API issues that may require manual investigation beyond auto-fix capabilities.

## Recommendation
Monitor over next 3 days. If health score doesn't improve above 0.3, investigate tool_call configuration and API endpoints manually.
