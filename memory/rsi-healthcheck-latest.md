# RSI Loop Health Check — 2026-03-30 03:00 AEDT

## Summary
- **Health Score:** 0.096 / 1.0 ⚠️ CRITICAL (threshold: 0.3)
- **Outcomes (7d):** 260 logged | Success rate: 23% | Avg quality: 2.08/5
- **Tests:** ✅ 32/32 passed

## Top Issues
| Issue | Count | Failure Rate |
|-------|-------|-------------|
| timeout | 78 | 100% |
| tool_error | 77 | 100% |
| tool_validation_error | 36 | 100% |
| context_loss | 60 | — |

## Patterns Detected (6)
1. [0.900] In 'tool_call' tasks, 'timeout' occurs 78x with 100% failure rate
2. [0.888] In 'tool_call' tasks, 'tool_error' occurs 77x with 100% failure rate
3. [0.554] In 'tool_call' tasks, 'tool_validation_error' occurs 36x with 100% failure rate
4. Additional patterns on context_loss and model routing

## Cycle Results
- Proposals generated: 5 (all already deployed)
- Auto-deployed: 0 (nothing new to deploy)
- Awaiting review: 0

## Deployed Proposals (pending effect)
- db32089a: Address 'timeout' in 'tool_call' tasks
- b9e26a71: Address 'tool_error' in 'tool_call' tasks
- 15c31c37: Address 'tool_validation_error' in 'tool_call' tasks
- 3a2dc2d1: Fix model routing rate limits

## Assessment
Health score remains critically low at 0.096. The deployed proposals have not yet reduced the failure rates — timeout, tool_error, and tool_validation_error collectively account for ~75% of failures. The core issue is persistent tool_call failures (timeouts + errors) in the 7-day window. 

**Next action:** Review whether deployed proposals are actually being applied in production. The pattern may require deeper intervention — e.g., reducing concurrent tool calls, adjusting timeout values, or fixing tool parameter validation upstream.
