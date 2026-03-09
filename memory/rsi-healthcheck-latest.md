# RSI Loop Health Check Report
**Date:** 2026-03-09 03:00:00 AEDT
**Cron Job:** rsi-loop-health-check (nightly)

## Health Status: ⚠️ ALERT - Health Score 0.1 (Critical)

### System Status
- **Outcomes (7d):** 181 logged
- **Success Rate:** 27% (very low)
- **Avg Quality:** 1.85/5 (poor)
- **Health Score:** 0.1/1.0 (critical threshold: <0.3)
- **Patterns Detected:** 5
- **Proposals:** 22 deployed, 0 pending

### Top Failure Patterns (Last 7 Days)

1. **[1.823] 'none' outcome in 'tool_call' tasks**
   - Occurrences: 83x
   - Failure rate: 100%
   - Impact: Critical
   - Likely cause: Agents not logging outcomes properly or tasks failing silently

2. **[0.746] 'tool_error' in 'tool_call' tasks**
   - Occurrences: 45x
   - Failure rate: 100%
   - Impact: High
   - Likely cause: Tool execution errors, missing tools, or incorrect tool usage

3. **[0.514] 'context_loss' in 'session_management' tasks**
   - Occurrences: 47x
   - Failure rate: 0% (detected but not necessarily failures)
   - Impact: Medium
   - Note: May be expected behavior for session resets

### Minor Issues
- Rate limit errors: 2x (100% failure, but low volume)

### Test Results
✅ All 32 tests PASSED (0.82s)
- Auto-observe classification: ✅
- Recurrence detection: ✅
- Auto-fix proposal generation: ✅
- Codebase search: ✅

### RSI Cycle Actions Taken
- **Generated proposals:** 5
- **Auto-approved:** 1 (proposal 0041c57f - rate limit fix, <20min effort)
- **Deployed:** 1 (with minor status warning - already deployed)
- **Awaiting review:** 0

### Recommendation

🔔 **ALERT:** Health score (0.1) is below critical threshold (0.3). Immediate attention needed.

**Priority actions:**
1. Investigate why 83 'tool_call' tasks resulted in 'none' outcomes - agents may not be logging properly
2. Address 45 'tool_error' failures - check tool configuration and usage patterns
3. Review outcome logging discipline across sub-agents
4. Consider implementing outcome validation to prevent silent 'none' results

**Next steps:**
- Review auto-generated proposals in `skills/rsi-loop/proposals/`
- Check agent logs for tool_error details
- Verify outcome logging is working correctly across all agents
