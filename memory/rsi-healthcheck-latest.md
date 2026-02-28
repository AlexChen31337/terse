# RSI Loop Health Check Report
**Date:** 2026-02-28 03:00:00 AEDT
**Status:** ⚠️ HEALTH SCORE BELOW THRESHOLD

## Health Score
- **Current:** 0.133 (13.3%)
- **Threshold:** 0.30 (30%)
- **Verdict:** ❌ BELOW THRESHOLD - ALERT REQUIRED

## Outcomes Analysis (7 days)
- **Total logged:** 147 outcomes
- **Success rate:** 30%
- **Average quality:** 2.22/5

### Top Failure Patterns
| Pattern | Occurrences | Failure Rate |
|---------|-------------|--------------|
| tool_error | 51 | - |
| context_loss | 28 | 4% |
| wal_miss | 11 | - |

### High-Confidence Patterns (score > 0.3)
- **[0.965]** In 'unknown' tasks, 'tool_error' occurs 45x with 100% failure rate
- **[0.937]** In 'unknown' tasks, 'none' occurs 38x with 89% failure rate
- **[0.373]** In 'unknown' tasks, 'context_loss' occurs 26x with 4% failure rate

## Proposals Status
- **Draft:** 1
- **Approved:** 1
- **Deployed:** 14

### Ready to Deploy
- `b1b44540`: Fix: In 'monitoring' tasks, 'cost_overrun' occurs 1x with 10

### Auto-Cycle Issues
The auto-cycle encountered an error during deployment phase:
```
FileNotFoundError: Proposal '4d46d054' not found
```
This suggests a race condition where the proposal list changed between synthesis and deployment.

## Test Results
✅ **All tests passed (32/32)**
- test_auto_observe.py: 21 passed
- test_auto_fix.py: 11 passed
- Duration: 0.76s

## Recommendations
1. **URGENT:** Address the 'tool_error' pattern in 'unknown' tasks (45 occurrences, 100% failure)
2. **URGENT:** Fix the 'none' pattern in 'unknown' tasks (38 occurrences, 89% failure)
3. Fix the auto-cycle deployment bug (proposal file not found)
4. Review 'context_loss' pattern (28 occurrences, though low failure rate)

## Next Action Required
🚨 **Health score (0.133) is below threshold (0.30)** - Manual intervention recommended.

Run the following to deploy pending fixes:
```bash
uv run python skills/rsi-loop/scripts/rsi_cli.py deploy b1b44540
```

Or review all proposals:
```bash
uv run python skills/rsi-loop/scripts/rsi_cli.py proposals
```
