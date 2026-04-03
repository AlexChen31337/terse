# RSI Health Check — 2026-04-03 03:10 AEDT

## Status Summary
- **Health Score: 0.095** ⚠️ CRITICAL (threshold: 0.3)
- **7-Day Outcomes:** 137 logged
- **Success Rate:** 22%
- **Avg Quality:** 2.18 / 5

## Top Issues
| Issue | Count | Failure Rate |
|-------|-------|-------------|
| timeout | 52 | 100% |
| tool_error | 42 | 100% |
| context_loss | 30 | 0% |

## Detected Patterns (5)
1. **[1.136]** In `tool_call` tasks, `timeout` occurs 53x with 100% failure rate
2. **[0.921]** In `tool_call` tasks, `tool_error` occurs 43x with 100% failure rate
3. **[0.443]** In `session_management` tasks, `context_loss` occurs 31x with 0% failure

## Proposals
- **1 draft | 0 approved | 24 deployed**
- Cycle generated 5 proposals — all already deployed or auto-approved
- No new proposals pending review

## Deployed Auto-Fixes (still in effect)
- `db32089a` — Address 'timeout' in tool_call tasks
- `b9e26a71` — Address 'tool_error' in tool_call tasks
- `3a2dc2d1` — Fix model routing rate limits
- `15c31c37` — Address 'tool_validation_error' in tool_call tasks

## Assessment
Despite 24 deployed proposals, the health score remains critical at 0.095. The dominant failure modes (timeout, tool_error) persist. The deployed fixes may not be addressing root causes, or new failures are outpacing fixes. Success rate of only 22% indicates systemic issues.
