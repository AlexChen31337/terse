# RSI Loop Health Check Report
**Date:** 2026-03-10 03:00:00 AEDT
**Status:** ⚠️ LOW HEALTH

## Metrics
- **Health Score:** 0.114 / 1.0 (CRITICAL, threshold: 0.3)
- **Outcomes (7d):** 158 logged
- **Success Rate:** 28% (target: >70%)
- **Avg Quality:** 1.99 / 5 (target: >3.5)

## Top Failure Patterns
1. **[1.405]** tool_call → 'none' outcome: 57 occurrences, 100% failure
2. **[1.025]** tool_call → 'tool_error': 54 occurrences, 100% failure
3. **[0.551]** session_management → 'context_loss': 44 occurrences, 0% failure (quality issue)
4. **[N/A]** model_routing → 'rate_limit': 2 occurrences, 100% failure

## Proposals Generated This Cycle
- **b9e26a71:** Address 'tool_error' in 'tool_call' tasks (draft)
- **0041c57f:** Fix rate_limit in 'model_routing' tasks (auto-approved, deployment failed - status was 'deployed' not 'approved')

## Test Results
✅ All 32 tests passed (test_auto_observe.py + test_auto_fix.py)

## Action Required
- **Critical:** Health score 0.114 is well below 0.3 threshold
- **Priority:** Fix tool_call failures (57 + 54 = 111 failures, 70% of total outcomes)
- **Investigation:** Proposal 0041c57f deployment error - status workflow issue

## Recommendations
1. Investigate why 'none' outcomes dominate tool_call tasks
2. Review tool_error handling and error recovery
3. Fix proposal deployment status check (deployed vs approved race condition)
