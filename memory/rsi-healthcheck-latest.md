# RSI Loop Health Check — 2026-04-14T03:11 AEST

## Status
- **Health Score:** 0.177 ⚠️ (threshold: 0.3)
- **7-Day Outcomes:** 23 logged
- **Success Rate:** 39%
- **Avg Quality:** 2.26/5

## Top Issues
| Issue | Count | Fail Rate | Domain |
|-------|-------|-----------|--------|
| context_loss | 9 | 0% | session_management |
| tool_validation_error | 8 | 100% | tool_call |
| incomplete_task | 4 | 100% | message_routing |

## Patterns Detected (4)
1. **[1.391]** In 'tool_call' tasks, 'tool_validation_error' occurs 8x with 100% fail
2. **[0.696]** In 'message_routing' tasks, 'incomplete_task' occurs 4x with 100% fail
3. **[0.391]** In 'session_management' tasks, 'context_loss' occurs 9x with 0% failure

## Proposals
- **Draft:** 1 (awaiting review)
- **Approved:** 0
- **Deployed:** 24 total (3 skipped in this cycle as already deployed)

## Latest Cycle Result
- 4 proposals generated
- 0 auto-deployed (all already deployed or needs review)
- Pending review: 1 proposal (`uv run python skills/rsi-loop/scripts/synthesizer.py list`)

## Action Taken
- ⚠️ Alert sent to Bowen via Telegram (score < 0.3)
