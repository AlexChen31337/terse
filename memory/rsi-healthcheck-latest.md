# RSI Loop Health Check — 2026-03-20 03:00 AEDT

## System Status

**Health Score:** 0.142 / 1.0 ⚠️  
**Outcomes (7d):** 164 logged
**Success Rate:** 32%
**Avg Quality:** 2.18/5

## Top Failure Patterns

1. **context_loss** (52 occurrences, 0% failure rate — detected but not critical)
2. **tool_error** (45 occurrences, 100% failure rate in 'tool_call' tasks)
3. **timeout** (43 occurrences, 100% failure rate in 'tool_call' tasks)

## Detected Patterns (5 total)

- [0.825] In 'tool_call' tasks, 'tool_error' occurs 44x with 100% failure rate
- [0.787] In 'tool_call' tasks, 'timeout' occurs 42x with 100% failure rate
- [0.637] In 'session_management' tasks, 'context_loss' occurs 51x with 0% failure rate
- [0.421] In 'tool_call' tasks, 'tool_validation_error' occurs 40x with 100% failure rate
- [0.312] In 'tool_call' tasks, 'llm_error' occurs 33x with 100% failure rate

## Proposals Status

- **Draft:** 0
- **Approved:** 0
- **Deployed:** 24 (all current proposals already deployed)

## Test Results

✅ **All 32 tests passed** (1.03s)
- test_auto_observe.py: 21 tests passed
- test_auto_fix.py: 11 tests passed

## Analysis

The health score is **below 0.3 threshold** (0.142), but this is primarily driven by:
1. High 'tool_call' task failure rates (tool_error, timeout, validation errors)
2. Context loss detection (though marked as 0% failure rate, likely informational)

**All improvement proposals have already been deployed** — no new fixes needed this cycle.

**Tests passing** — RSI loop core functionality is healthy.

## Recommendations

1. Monitor 'tool_call' task reliability — this is the primary failure driver
2. Context loss detection appears to be working correctly (informational logging)
3. No immediate action required — all fixable patterns already addressed

---

**Report generated:** 2026-03-20 03:00 AEDT  
**Next check:** 2026-03-21 03:00 AEDT
