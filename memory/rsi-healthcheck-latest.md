# RSI Loop Health Check Report
**Date:** 2026-03-02 03:00:00 AEDT
**Trigger:** Nightly cron (8cc932c5)

## Health Score
🚨 **0.119 / 1.0** — CRITICAL (below 0.3 threshold)

## Status Summary
- **Outcomes (7d):** 200 logged
- **Success rate:** 28% (very low)
- **Avg quality:** 2.11/5 (poor)
- **Patterns detected:** 11 issues

## Top Failure Patterns
| Pattern | Frequency | Failure Rate |
|---------|-----------|--------------|
| `tool_error` in 'unknown' tasks | 68x | 100% |
| `context_loss` in 'unknown' tasks | 46x | 0% |
| `none` in 'unknown' tasks | 60x | 98% |
| `rate_limit` in 'unknown' tasks | 9x | 100% |

## Proposals
- **Generated:** 5 proposals
- **Auto-approved:** 1 (5f54ae79)
- **Deployed:** 15 total proposals to date

## Deployment Error
⚠️ **Proposal '5f54ae79' not found** — Auto-approved proposal was generated but failed to deploy (FileNotFoundError).

## Auto-Fix Generated
6 new fix proposals drafted:
- [682e6962] Address 'tool_error' in 'unknown' tasks
- [c5a69afe] Fix 'rate_limit' in 'unknown' tasks
- [56638f19] Fix 'tool_error' in 'infrastructure_ops'
- [b1b44540] Fix 'cost_overrun' in 'monitoring'
- [2cea18f8] Fix 'wal_miss' in 'memory_retrieval'
- [8479eda7] Address 'wal_miss' in 'unknown' tasks

## Test Results
✅ **All 32 tests passed** (0.74s)

## Recommendations
1. Fix deployment bug — proposal not being saved before deploy
2. Investigate 'unknown' task classification — 60%+ of failures
3. Address 'tool_error' cascade — 68 occurrences

## Next Steps
Run manual review of proposals:
```bash
uv run python skills/rsi-loop/scripts/rsi_cli.py review
```
