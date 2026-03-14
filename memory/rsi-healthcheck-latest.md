# RSI Loop Health Check Report
**Generated:** 2026-03-15 03:00 AEDT (2026-03-14 16:00 UTC)
**Status:** ⚠️ CRITICAL — Health score below threshold

## Health Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Health Score | 0.134 / 1.0 | ⚠️ CRITICAL (threshold: 0.3) |
| 7-Day Outcomes | 148 logged | — |
| Success Rate | 31% | ❌ Poor |
| Avg Quality | 2.16 / 5 | ❌ Below average |
| Patterns Detected | 4 | — |
| Proposals Deployed | 24 total (0 new this cycle) | — |

## Critical Failure Patterns

### 1. Tool Call Errors (SEVERITY: 1.236)
- **Context:** 'tool_call' tasks
- **Issue:** 'tool_error' occurs 61 times
- **Failure Rate:** 100%
- **Impact:** HIGH — 41% of all logged outcomes

### 2. Tool Validation Errors (SEVERITY: 0.568)
- **Context:** 'tool_call' tasks
- **Issue:** 'tool_validation_error' occurs 21 times
- **Failure Rate:** 100%
- **Impact:** MEDIUM-HIGH — 14% of all logged outcomes

### 3. Context Loss (SEVERITY: 0.622)
- **Context:** 'session_management' tasks
- **Issue:** 'context_loss' occurs 46 times
- **Failure Rate:** 0% (appears to be non-fatal but frequent)
- **Impact:** MEDIUM — 31% of all logged outcomes

## Test Results

**Auto-Observe Tests:** ✅ All 20 tests passed
**Auto-Fix Tests:** ✅ All 12 tests passed
**Total:** 32/32 passed in 0.88s

## Cycle Actions

- **Proposals Generated:** 4 (all previously deployed)
- **Auto-Approved:** 0 (all already deployed)
- **New Deployments:** 0

## Recommendations

1. **IMMEDIATE:** Investigate `tool_error` in 'tool_call' tasks — this is the single largest failure pattern (41% of outcomes, 100% failure rate)
2. **URGENT:** Fix `tool_validation_error` pattern — 100% failure rate suggests systematic validation issues
3. **MEDIUM:** Address `context_loss` frequency — may require session architecture review
4. **LONG-TERM:** Target health score >0.7 by reducing overall failure rate below 20%

## Previous Deployments

The following proposals were already deployed in previous cycles:
- `b9e26a71` — Address 'tool_error' in 'tool_call' tasks
- `60126e7f` — Address 'context_loss' in 'session_management' tasks
- `15c31c37` — Address 'tool_validation_error' in 'tool_call' tasks
- `db32089a` — Address 'timeout' in 'tool_call' tasks

**Note:** The recurrence of these patterns suggests the deployed fixes may have been ineffective or the underlying issues are multi-factorial.
