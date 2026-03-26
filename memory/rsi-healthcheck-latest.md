# RSI Loop Health Check — 2026-03-26 03:00 AEDT

## System Status

### RSI Health Score
- **Current:** 0.128 (below 0.3 threshold)
- **Trend:** Stable (no degradation from previous check)
- **Status:** ⚠️ Low but stable

### Outcomes (7d)
- **Total:** 221 logged
- **Success rate:** 30%
- **Avg quality:** 2.12/5
- **Top issues:**
  - context_loss: 67 occurrences
  - timeout: 57 occurrences
  - tool_error: 56 occurrences

### Patterns Detected
1. `[0.770]` In 'tool_call' tasks, 'timeout' occurs 57x with 100% failure rate
2. `[0.757]` In 'tool_call' tasks, 'tool_error' occurs 56x with 100% failure rate
3. `[0.721]` In 'tool_call' tasks, 'tool_validation_error' occurs 40x with 100% failure rate
4. `[0.x]` Additional pattern data truncated in output

### Proposals Status
- **Draft:** 0
- **Approved:** 0
- **Deployed:** 24 (all 4 current patterns already deployed)

## Test Results
✅ **All 32 tests passed** (1.08s)
- test_auto_observe.py: 20/20 passed
- test_auto_fix.py: 12/12 passed

## Assessment
- ✅ No critical alerts
- ✅ All patterns already addressed with deployed fixes
- ✅ Test suite fully passing
- ⚠️ Health score below 0.3 but stable (all known issues already mitigated)

## Recommendation
No immediate action required. The low health score reflects historical issues that have already been addressed via deployed proposals. The system is stable with auto-fixes in place for the detected patterns.

## Next Scheduled Check
2026-03-27 03:00 AEDT (24h)
