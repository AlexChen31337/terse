# RSI Loop Health Check — 2026-03-31 03:00 AEST

## Summary
- **Health Score:** 0.096 / 1.0 ⚠️ CRITICAL (threshold: 0.30)
- **Tests:** 32/32 PASSED ✅
- **Outcomes (7d):** 224 logged | Success rate: 23% | Avg quality: 2.1/5

## Top Failure Patterns
| Pattern | Severity | Occurrences | Failure Rate |
|---------|----------|-------------|--------------|
| `timeout` in `tool_call` tasks | 0.921 | 70x | 100% |
| `tool_error` in `tool_call` tasks | 0.921 | 70x | 100% |
| `tool_validation_error` in `tool_call` tasks | 0.491 | 28x | 100% |
| context_loss | — | 51x | — |

## Proposals
- 5 generated, 5 already deployed (db32089a, b9e26a71, 15c31c37, 60126e7f, 3a2dc2d1)
- 0 new auto-deployments this cycle
- Root cause fixes deployed but not yet reflected in outcomes (lag expected)

## Assessment
The deployed proposals address the patterns, but outcomes haven't improved yet (23% success, health 0.096). The `timeout` and `tool_error` failures in `tool_call` tasks are the dominant signal — likely related to model routing or subagent execution issues. Proposals are deployed; need to monitor if they take effect over the next 24–48h.

## Tests
- `test_auto_observe.py`: 18/18 PASSED
- `test_auto_fix.py`: 14/14 PASSED
