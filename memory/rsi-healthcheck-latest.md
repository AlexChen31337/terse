# RSI Loop Health Check Report
**Date:** 2026-03-08 03:00 AEDT
**Trigger:** Nightly cron health check

## Status Summary

| Metric | Value | Status |
|--------|-------|--------|
| Health Score | 0.093 | ⚠️ Critical |
| Outcomes (7d) | 206 logged | 📊 Normal |
| Success Rate | 26% | 🔴 Poor |
| Avg Quality | 1.8/5 | 🔴 Poor |
| Tests | 32/32 passed | ✅ Pass |

## Top Failure Patterns (Last 7 Days)

1. **[1.602] tool_call → none** (83 occurrences, 100% failure)
   - Pattern: Tool calls returning no response
   - Impact: HIGH
   - Status: Auto-fix proposal generated

2. **[0.641] tool_call → tool_error** (44 occurrences, 100% failure)
   - Pattern: Tool errors during execution
   - Impact: HIGH
   - Status: Auto-fix proposal generated

3. **[0.490] session_management → context_loss** (51 occurrences, 0% failure)
   - Pattern: Session context loss events (non-fatal but disruptive)
   - Impact: MEDIUM
   - Status: Monitoring

4. **[0.361] model_routing → rate_limit** (2 occurrences, 100% failure)
   - Pattern: Model provider rate limits
   - Impact: MEDIUM
   - Status: Auto-approved fix (20min effort)

## Proposals Generated

This cycle generated 5 proposals:
- **Auto-approved:** 1 (rate_limit fix, 20min effort)
- **Awaiting review:** 0
- **Deployed:** 22 (historical)

## Test Results

All 32 tests passed:
- test_auto_observe.py: 20/20 ✅
- test_auto_fix.py: 12/12 ✅

## Recommendations

**IMMEDIATE ACTION REQUIRED:**
- Health score (0.093) is well below 0.3 threshold
- 26% success rate indicates significant operational issues
- Tool errors and no-response events are dominating failures

**Next Steps:**
1. Review auto-generated proposals in `skills/rsi-loop/proposals/`
2. Prioritize the "tool_call → none" fix (highest impact)
3. Investigate tool error root causes (possibly model-related)
4. Consider reducing tool call frequency or adding fallbacks

## System Health

- RSI Loop: ✅ Operational (cycle ran successfully)
- Tests: ✅ All passing
- Proposals: ✅ Generation working
- Deployment: ⚠️ One deployment error (proposal status issue)

---

**Report saved:** `memory/rsi-healthcheck-latest.md`
