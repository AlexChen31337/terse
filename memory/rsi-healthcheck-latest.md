# RSI Loop Health Check Report

**Date:** Friday, March 6th, 2026 — 3:00 AM AEDT
**Trigger:** Nightly cron health check

## Health Score

**Current Score: 0.087 / 1.0** ⚠️ CRITICAL (threshold: < 0.3)

## Status Summary

- **Outcomes (7d):** 234 logged
- **Success Rate:** 24% (very low)
- **Avg Quality:** 1.82/5
- **Patterns Detected:** 6
- **Proposals Generated:** 5
- **Auto-Approved:** 1 (3a2dc2d1 - "Fix model routing rate limits")
- **Proposals Deployed:** 22 (all-time)

## Top Issues (Last 7 Days)

1. **tool_error** (56 occurrences) — highest priority
2. **context_loss** (54 occurrences)
3. **rate_limit** (11 occurrences)

## Top Patterns Detected

1. **[1.318]** In 'tool_call' tasks, 'none' occurs 78x with 100% failure rate
2. **[0.725]** In 'tool_call' tasks, 'tool_error' occurs 57x with 100% failure rate
3. **[0.538]** In 'unknown' tasks, 'none' occurs 33x with 100% failure rate

## Auto-Fix Proposals Generated This Cycle

- `b9e26a71`: Address 'tool_error' in 'tool_call' tasks
- `3a2dc2d1`: [Gene] Fix model routing rate limits (auto-approved)
- `0041c57f`: Fix: In 'model_routing' tasks, 'rate_limit' occurs 2x with 100% failure

## Test Results

**Status:** ✅ ALL PASSED (32/32 tests in 0.76s)

- `test_auto_observe.py`: 19 tests passed
- `test_auto_fix.py`: 13 tests passed

## Alert Status

🚨 **HEALTH SCORE BELOW THRESHOLD** — 0.087 < 0.3

**Recommendation:** Alert required — Bowen should review top patterns and consider deploying the pending proposals.

## Next Steps

1. Review the 3 proposals generated this cycle
2. Address the 'tool_error' pattern in 'tool_call' tasks (57 failures)
3. Investigate high context_loss rate (54 occurrences)
4. Consider deployment of auto-approved proposal 3a2dc2d1
