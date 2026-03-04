# RSI Loop Health Check Report
**Date:** 2026-03-04 03:00 AEDT
**Trigger:** Nightly cron health check

## Health Score
**Current Score:** 0.102 / 1.0 ⚠️ **BELOW THRESHOLD (0.3)**

## Status Summary
- **Outcomes (7d):** 206 logged
- **Success Rate:** 27% (very low)
- **Avg Quality:** 1.91/5 (poor)
- **Patterns Detected:** 7
- **Proposals:** 1 draft | 0 approved | 20 deployed

## Top Failure Patterns (Last 7 Days)
1. **[0.971 severity]** In 'tool_call' tasks, 'none' occurs 50x with 100% failure rate
2. **[0.801 severity]** In 'tool_call' tasks, 'tool_error' occurs 55x with 100% failure rate
3. **[0.636 severity]** In 'unknown' tasks, 'none' occurs 34x with 100% failure rate
4. rate_limit (9 occurrences)
5. context_loss (51 occurrences)

## RSI Cycle Results
- ✅ Analysis completed
- ✅ Synthesis completed (5 proposals generated)
- ✅ Auto-approval phase completed (1 proposal auto-approved: 55d06296)
- ❌ **DEPLOYMENT FAILED** - FileNotFoundError: Proposal '55d06296' not found
- Auto-fix phase generated 3 additional draft proposals

## Test Results
✅ **All 32 tests PASSED** (0.75s)
- test_auto_observe.py: 19/19 passed
- test_auto_fix.py: 13/13 passed

## Issues Requiring Attention
1. **Critical:** Deployment failure - auto-approved proposal 55d06296 was not found during deployment
2. **High failure rate:** 73% of tasks failing in last 7 days
3. **Tool errors:** 55 tool_call failures with 'tool_error' outcome
4. **Context loss:** 51 occurrences affecting task continuity

## Recommendations
1. Investigate why auto-approved proposals are not being saved before deployment
2. Address the 'tool_error' pattern in tool_call tasks (top failure mode)
3. Review context loss mitigation strategies
4. Consider health score reset if historical patterns are outdated

## Auto-Fix Proposals Generated
- b9e26a71: Address 'tool_error' in 'tool_call' tasks
- 3a2dc2d1: [Gene] Fix model routing rate limits
- b1b44540: Fix: In 'monitoring' tasks, 'cost_overrun' occurs 1x with 100% failure

---
**Report saved by:** RSI Loop Health Check (cron:8cc932c5)
**Next check:** 2026-03-05 03:00 AEDT
