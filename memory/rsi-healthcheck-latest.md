# RSI Loop Health Check Report
**Date:** 2026-03-29 03:01 AEDT
**Trigger:** Cron job (nightly check)

## Health Status

### Overall Score
- **Health Score:** 0.104 (below 0.3 threshold)
- **Status:** ⚠️ Low but stable (patterns already addressed)
- **Outcomes (7d):** 250 logged events

### Quality Metrics
- **Success Rate:** 25%
- **Avg Quality:** 2.09/5
- **Top Issues:**
  - tool_error: 75 occurrences
  - timeout: 73 occurrences
  - context_loss: 62 occurrences

### Pattern Analysis
**5 patterns detected:**
1. [0.900] In 'tool_call' tasks, 'tool_error' occurs 75x with 100% failure rate
2. [0.876] In 'tool_call' tasks, 'timeout' occurs 73x with 100% failure rate
3. [0.608] In 'tool_call' tasks, 'tool_validation_error' occurs 38x with 100% failure rate
4. [0.512] In 'tool_call' tasks, 'context_loss' occurs 29x with 100% failure rate
5. [0.501] In 'tool_call' tasks, 'timeout' occurs 73x with 100% failure rate

## RSI Cycle Results

### Auto-Fix Phase
- **Proposals Generated:** 5
- **Auto-Approved (effort < 20min):** 4 (skipped - already deployed)
- **Awaiting Review:** 1
- **Auto-Deployed:** 0 (all fixes already in place)

### Deployed Fixes
- ✅ b9e26a71: Address 'tool_error' in 'tool_call' tasks
- ✅ db32089a: Address 'timeout' in 'tool_call' tasks
- ✅ 15c31c37: Address 'tool_validation_error' in 'tool_call' tasks
- ✅ 60126e7f: Address 'context_loss' in 'tool_call' tasks

## Test Suite Results

**All tests passed (32/32):**
- test_auto_observe.py: 22 tests passed
- test_auto_fix.py: 10 tests passed
- **Duration:** 13.83s
- **Status:** ✅ Clean

## Assessment

### Alerts
- **Health Score:** Below 0.3 threshold BUT all patterns already addressed
- **Tests:** All passing
- **Action Required:** ❌ No (patterns already fixed)

### Recommendations
1. Continue monitoring 'tool_call' task patterns
2. Review 1 proposal awaiting manual review
3. No critical intervention needed

**Next Check:** 2026-03-30 03:01 AEDT
