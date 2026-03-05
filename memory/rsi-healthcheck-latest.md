# RSI Loop Health Check Report
**Date:** 2026-03-05 03:00 AEDT
**Status:** ⚠️ HEALTH ALERT — Health score 0.094 < 0.3 threshold

## Status Summary
- **Health Score:** 0.094 / 1.0 (CRITICAL — below 0.3 threshold)
- **Outcomes (7d):** 245 logged
- **Success Rate:** 25%
- **Avg Quality:** 1.87/5

## Top Failure Patterns (Detected)
1. **[1.257]** In 'tool_call' tasks, 'none' occurs 77x with 100% failure rate
2. **[0.722]** In 'tool_call' tasks, 'tool_error' occurs 59x with 100% failure rate
3. **[0.535]** In 'unknown' tasks, 'none' occurs 34x with 100% failure rate

**Top Issues (7d):**
- tool_error: 59 occurrences
- context_loss: 57 occurrences
- rate_limit: 11 occurrences

## Auto-Fix Cycle Results
- **Patterns Found:** 7
- **Proposals Generated:** 5
- **Auto-Approved:** 1 (3a2dc2d1 — model routing rate limits, 20min effort)
- **Deployed:** 0 (deployment failed: status was already 'deployed')
- **Awaiting Review:** 4 proposals

### Generated Proposals
1. **b9e26a71** — Address 'tool_error' in 'tool_call' tasks
2. **3a2dc2d1** — Fix model routing rate limits [Gene]
3. **0041c57f** — Fix rate_limit in 'model_routing' tasks

## Test Results
✅ All tests passed (32/32 in 0.72s)
- test_auto_observe.py: 21 passed
- test_auto_fix.py: 11 passed

## Action Required
⚠️ **Health score 0.094 < 0.3 threshold — Bowen notified**

### Immediate Actions Recommended
1. Review the 4 pending proposals with: `uv run python skills/rsi-loop/scripts/synthesizer.py list`
2. Investigate the 'tool_call' + 'tool_error' pattern (59 occurrences, 100% failure)
3. Fix the deployment bug (proposal status transitions incorrectly)
4. Address context_loss issues (57 occurrences — likely compaction-related)

## Deployment Stats
- Total Proposals: 22 deployed, 4 pending review
- Deployed Proposals: 22

---
*Report saved automatically by RSI Loop health check cron*
