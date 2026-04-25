# RSI Loop Health Check — 2026-04-25 03:15 AEST

## Status
- **Health Score:** 0.224 ⚠️ (threshold: 0.3)
- **Outcomes (7d):** 64 logged
- **Success Rate:** 42%
- **Avg Quality:** 2.75/5

## Top Issues
1. `tool_error` — 29 occurrences (100% failure rate in tool_call tasks)
2. `context_loss` — 27 occurrences (session_management)
3. `tool_validation_error` — 4 occurrences

## Patterns Detected (4)
1. **[1.368]** In tool_call tasks, tool_error occurs 31x with 100% failure rate
2. **[0.412]** In session_management tasks, context_loss occurs 28x with 0% failure rate
3. **[0.265]** In message_routing tasks, incomplete_task occurs 5x with 100% failure rate
4. *(1 more lower-significance pattern)*

## Cycle Results
- Proposals generated: 4
- Auto-deployed: 0 (all already deployed)
- Awaiting review: 0
- Two existing repair mutations active: `b9e26a71` (tool_error), `15c31c37` (tool_validation_error)

## Action
- ⚠️ **Alerting Bowen** — health score 0.224 < 0.3 threshold
- Main concern: tool_error pattern has 100% failure rate despite existing repair mutation
- May need manual investigation of tool_call failures
