# RSI Loop Health Check Report
**Date:** 2026-03-03 03:00
**Status:** ⚠️ HEALTH SCORE BELOW THRESHOLD

## Health Score
**0.104 / 1.0** (threshold: 0.3) — **ACTION REQUIRED**

## Status Summary
- Outcomes (7d): 209 logged
- Success rate: 27%
- Avg quality: 1.95/5

## Top Issues (Patterns Detected)
1. **[0.934]** 'unknown' tasks → 'none' failure (51 occurrences, 100% failure)
2. **[0.877]** 'tool_call' tasks → 'tool_error' failure (62 occurrences, 100% failure)
3. **[0.585]** 'tool_call' tasks → 'none' failure (31 occurrences, 100% failure)
4. rate_limit (9 occurrences)
5. context_loss (50 occurrences)

## Proposals
- Drafts: 1
- Approved: 1
- Deployed: 19

**Ready to deploy:**
- `60126e7f`: Improve memory continuity for 'session_management'
  Deploy command: `uv run python skills/rsi-loop/scripts/rsi_cli.py deploy 60126e7f`

## Auto-Cycle Results
- Generated 5 proposals
- Auto-approved: 1 proposal (cc7b7b1d, 20min effort)
- **Deployment failed:** Proposal file not found (cc7b7b1d)
- 3 additional fix proposals drafted:
  - b9e26a71: Address 'tool_error' in 'tool_call' tasks
  - 3a2dc2d1: [Gene] Fix model routing rate limits
  - b1b44540: Fix 'cost_overrun' in 'monitoring' tasks

## Test Results
✅ **All 32 tests passed** (0.73s)
- test_auto_observe.py: 22 passed
- test_auto_fix.py: 10 passed

## Recommendations
1. **Investigate 'tool_error' in 'tool_call' tasks** — 62 failures, highest priority
2. **Fix 'unknown' task classification** — 51 failures with 100% rate
3. **Review proposal deployment pipeline** — auto-approved proposal failed to deploy
4. **Consider deploying proposal 60126e7f** — memory continuity improvement
5. **Address context_loss issues** — 50 occurrences over 7 days

## Next Actions
1. Run full analysis: `uv run python skills/rsi-loop/scripts/rsi_cli.py analyze`
2. Review tool_error pattern details
3. Fix deployment pipeline bug (proposal file not found after auto-approval)
4. Deploy memory continuity proposal if approved
