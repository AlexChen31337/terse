# RSI Loop Health Check Report
**Generated:** 2026-03-16 03:00 AEDT (2026-03-15 16:00 UTC)
**Cycle:** Nightly automated check

## System Status

### Health Score
**Current: 0.124 / 1.0** ⚠️ LOW
- Threshold for alert: < 0.3
- Status: **Below healthy threshold**

### Outcomes Analysis (7 days)
- **Total logged:** 150 outcomes
- **Success rate:** 29% (43 successes / 150 total)
- **Average quality:** 2.12 / 5

### Detected Failure Patterns

1. **[1.100] tool_call → tool_error** (Severity: Critical)
   - Occurrences: 55 times
   - Failure rate: 100%
   - Impact: Highest confidence pattern

2. **[0.667] tool_call → tool_validation_error** (Severity: High)
   - Occurrences: 25 times
   - Failure rate: 100%

3. **[0.587] session_management → context_loss** (Severity: Medium)
   - Occurrences: 44 times
   - Failure rate: 0% (non-critical but frequent)

4. **[0.xxx] tool_call → timeout** (Severity: Medium)
   - Occurrences: 25 times
   - Failure rate: N/A

### Proposals Status
- **Generated:** 4 proposals (all repair type)
- **Status:** All already deployed
  - b9e26a71: tool_error fixes (deployed)
  - 15c31c37: tool_validation_error fixes (deployed)
  - 60126e7f: timeout fixes (deployed)
  - db32089a: additional tool_call fixes (deployed)

## Test Results
**Status:** ✅ ALL PASSED
- 32/32 tests passed in 0.88s
- Coverage: auto_observe, auto_fix, pattern detection, proposal generation

## Analysis

### Why is health score low despite deployed fixes?
The patterns detected are from historical outcomes (last 7 days). The proposals were already deployed, but:
1. Newly deployed fixes haven't yet produced enough positive outcomes to shift the 7-day rolling average
2. The 150 outcomes analyzed include pre-fix failures
3. Health score is a lagging indicator (7-day window)

### Positive Indicators
- ✅ Test suite fully passing
- ✅ Proposals generated and deployed correctly
- ✅ Auto-fix cycle completing successfully
- ✅ No new unsafe proposals generated

### Recommendations
1. **Monitor over next 3-5 days** — Health score should improve as fixed outcomes accumulate
2. **Check tool_error root cause** — 100% failure rate suggests systematic issue (may need infrastructure fix, not just skill updates)
3. **Review context loss pattern** — 44 occurrences is high even if non-critical

## Alert Status
**🔴 BELOW THRESHOLD** — Health score 0.124 < 0.3
**Decision:** Report to Bowen (this report serves as the alert)
