# RSI Loop Health Check Report
**Date:** 2026-02-27 03:00:00 AEDT
**Status:** ⚠️ CRITICAL - Health score below threshold (0.156 < 0.3)

## Executive Summary
- **Health Score:** 0.156 (CRITICAL - below 0.3 threshold)
- **Tests:** ✅ All 32 tests passed
- **7-Day Outcomes:** 115 logged
- **Success Rate:** 34%
- **Avg Quality:** 2.3/5

## Top Failure Patterns (Last 7 Days)
1. **tool_error (34 occurrences)** - 100% failure rate in unknown tasks
2. **context_loss (21 occurrences)** - 5% failure rate in unknown tasks
3. **wal_miss (11 occurrences)** - scattered across tasks

## RSI Cycle Results
- **Patterns Detected:** 17
- **Proposals Generated:** 5
- **Auto-Approved:** 0 (all require manual review)
- **Awaiting Review:** 5 proposals

### Awaiting Review Proposals
- 682e6962: Address 'tool_error' in 'unknown' tasks
- 8479eda7: Address 'wal_miss' in 'unknown' tasks
- c98028aa: Address 'cost_overrun' in 'trading' tasks
- f4533796: Address 'wal_miss' in 'trading' tasks
- 1d3f9b39: Address 'tool_error' in 'trading' tasks
- 989cb2b1: Address 'empty_response' in 'code_debug' tasks
- 56638f19: Fix: In 'infrastructure_ops' tasks, 'tool_error' occurs 1x with 100% failure
- b1b44540: Fix: In 'monitoring' tasks, 'cost_overrun' occurs 1x with 100% failure
- 2cea18f8: Fix: In 'memory_retrieval' tasks, 'wal_miss' occurs 1x with 100% failure

## Test Results
✅ All 32 tests passed (test_auto_observe.py + test_auto_fix.py)
- Test coverage: auto-observe, auto-fix, pattern detection, proposal generation
- Execution time: 0.70s

## Recommendations
1. **URGENT:** Review and address the high tool_error rate (34 occurrences, 100% failure)
2. Review pending proposals with: `uv run python skills/rsi-loop/scripts/synthesizer.py list`
3. Consider deploying ready proposal b1b44540 for monitoring cost_overrun fix
4. Investigate context_loss patterns affecting task continuity
5. Address wal_miss issues to improve outcome tracking accuracy

## System Health
- ✅ RSI Loop operational
- ✅ Auto-observe functional
- ✅ Auto-fix generating proposals
- ⚠️ Health score critically low - needs immediate attention
