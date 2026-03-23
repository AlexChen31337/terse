# RSI Loop Health Check Report
**Date:** 2026-03-23 03:00 AEDT / 2026-03-22 16:00 UTC
**Trigger:** Nightly cron job

## Health Score: 0.163 / 1.0 ⚠️

### Outcomes (7 days)
- **Total logged:** 178
- **Success rate:** 36%
- **Avg quality:** 2.27/5
- **Issues detected:** 162

### Top Failure Patterns
1. **context_loss** (63 occurrences) — session resets, compaction events
2. **timeout** (54 occurrences) — long-running operations exceeded limits
3. **tool_error** (45 occurrences) — tool invocation failures

### Patterns Detected (5)
1. `[0.912]` In 'tool_call' tasks, 'timeout' occurs 55x with 100% failure rate
2. `[0.762]` In 'tool_call' tasks, 'tool_error' occurs 46x with 100% failure rate
3. `[0.707]` In 'session_management' tasks, 'context_loss' occurs 64x with 0% failure rate
4. `[0.618]` In 'tool_call' tasks, 'tool_validation_error' occurs 11x with 100% failure rate
5. `[0.556]` In 'tool_call' tasks, 'unknown' occurs 32x with 81% failure rate

### Proposals
- **Draft:** 0
- **Approved:** 0
- **Deployed:** 24 (all current proposals already deployed)

### Cycle Results
- Full RSI cycle completed successfully
- 5 proposals generated (all already deployed)
- 0 new proposals requiring deployment
- Auto-fix phase checked 3 deployed fixes

### Test Results
- **Tests run:** 32
- **Passed:** 32 ✅
- **Failed:** 0
- **Duration:** 1.04s

### Assessment
**CRITICAL:** Health score (0.163) is below the 0.3 threshold.

**Primary concerns:**
1. High failure rate in 'tool_call' tasks (55+46+11 = 112 timeout/tool_error/validation failures)
2. 64 context_loss events indicating session instability
3. Low overall success rate (36%) and quality (2.27/5)

**Recommendation:** Bowen should review the deployed fixes and consider deeper architectural improvements to tool_call reliability and session persistence.

### Next Steps
1. Review deployed proposal details: `uv run python skills/rsi-loop/scripts/rsi_cli.py proposals`
2. Investigate tool_call timeout root causes
3. Consider session hardening to reduce context_loss events
