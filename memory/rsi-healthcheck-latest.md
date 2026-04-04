# RSI Health Check — 2026-04-04 03:10 AEDT

## Status Summary
- **Health Score: 0.089** ⚠️ CRITICAL (threshold: 0.3)
- **Outcomes (7d):** 102 logged
- **Success Rate:** 21%
- **Avg Quality:** 2.16/5

## Top Issues
| Issue | Count | Failure Rate |
|-------|-------|-------------|
| timeout | 39 | 100% |
| tool_error | 30 | 100% |
| context_loss | 21 | 0% |

## Detected Patterns (5)
1. **[1.167]** `tool_call` → `timeout` occurs 42x, 100% failure
2. **[0.861]** `tool_call` → `tool_error` occurs 31x, 100% failure
3. **[0.407]** `session_management` → `context_loss` occurs 22x

## RSI Cycle Result
- Proposals generated: 5
- Auto-deployed: 0 (all already deployed)
- Awaiting review: 0

## Deployed Proposals (not yet effective)
- `db32089a` — Address 'timeout' in tool_call tasks
- `b9e26a71` — Address 'tool_error' in tool_call tasks
- `3a2dc2d1` — Fix model routing rate limits
- `15c31c37` — Address 'tool_validation_error' in tool_call tasks

## Assessment
Health remains critical despite all proposals being deployed. The 21% success rate is driven by persistent timeouts and tool errors in tool_call tasks. Deployed fixes haven't moved the needle yet — may need manual investigation of root causes (proxy/API reliability, model routing configuration).
