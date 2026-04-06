# RSI Weekly Report — 2026-04-05

## Health Score: 0.129 🔴 (critical, <0.3)

## Outcomes (7 days)
- **Total:** 42 logged
- **Success rate:** 29%
- **Avg quality:** 2.26/5

## Top Issues
| Issue | Count | Failure Rate |
|-------|-------|-------------|
| context_loss | 12 | 0% (session_management) |
| timeout | 10 | 100% (tool_call) |
| tool_error | 9 | 100% (tool_call) |

## Patterns Detected (6)
1. **[0.714]** tool_call → timeout (10x, 100% failure)
2. **[0.643]** tool_call → tool_error (9x, 100% failure)
3. **[0.500]** session_management → context_loss (12x, 0% failure)

## Proposals
- **24 deployed**, **1 draft** (awaiting review), **2 rejected**
- Draft: `3b8e8f52` — Critical: Address 'incomplete_task' in 'message_routing' tasks (30min effort)
  - Pattern: 2 occurrences, 100% failure rate, seen 17 times (deduped)
  - Last seen: 2026-04-04

## Notes
- Low success rate driven primarily by tool_call timeouts and errors
- context_loss is frequent but not causing failures (likely compaction-related)
- Most proposals already deployed; the system is self-correcting but new failures keep appearing
- Root cause likely: infrastructural (model latency, rate limits) rather than agent logic
