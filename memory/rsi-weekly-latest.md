# RSI Weekly Report — 2026-03-08

## Executive Summary
- **Health Score:** 0.093 / 1.0 (CRITICAL — below 0.3 threshold)
- **Outcomes Analyzed:** 206 (last 7 days)
- **Success Rate:** 26%
- **Average Quality:** 1.8 / 5

## Critical Issues Detected

### Top Failure Patterns
1. **[1.602]** In 'tool_call' tasks, 'none' occurs 83x with 100% failure rate
2. **[0.641]** In 'tool_call' tasks, 'tool_error' occurs 44x with 100% failure rate
3. **[0.490]** In 'session_management' tasks, 'context_loss' occurs 51x

### Issue Breakdown (7d)
- **context_loss:** 51 occurrences
- **tool_error:** 44 occurrences
- **rate_limit:** 2 occurrences

## Proposals Generated
- **Total Generated:** 5 proposals
- **Auto-Approved:** 1 (20min effort)
- **Auto-Deployed:** 0 (deployment error - proposal status issue)
- **Awaiting Review:** 0

## Deployment Status
⚠️ **Deployment Issue:** Proposal 0041c57f failed to deploy (status was 'deployed' instead of 'approved')

## Recommendation
The health score of 0.093 is critically low. The dominant failure pattern is 'none' results in tool_call tasks (83 occurrences, 100% failure), suggesting tools are returning empty/undefined results systematically. This requires immediate investigation.

**Next Steps:**
1. Investigate why tools are returning 'none' results
2. Fix the proposal deployment status issue
3. Address context_loss patterns in session management

---
*Generated: 2026-03-08 03:00 AEDT*
