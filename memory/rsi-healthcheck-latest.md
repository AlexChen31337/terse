# RSI Loop Health Check — 2026-04-20 03:12 AEDT

## Status Summary
- **Health Score: 0.15** ⚠️ (threshold: 0.3)
- **Outcomes (7d):** 31 logged
- **Success Rate:** 32%
- **Avg Quality:** 2.32/5
- **Top Issues:** context_loss(10), tool_error(10), incomplete_task(7)
- **Patterns Detected:** 5
- **Proposals:** 1 draft, 0 approved, 24 deployed

## Top Patterns
1. `[0.968]` tool_call tasks → tool_error (10x, 100% failure)
2. `[0.903]` message_routing tasks → incomplete_task (7x, 100% failure)
3. `[0.387]` tool_call tasks → tool_validation_error (3x, 100% failure)

## Cycle Results
- 5 proposals generated, 0 auto-deployed (all already deployed or pending review)
- 1 proposal awaiting manual review
- Auto-fix notes: b9e26a71, 15c31c37, db32089a address tool errors/timeout

## Action Needed
- Health score well below 0.3 threshold
- Bowen notified via Telegram
- Manual review of pending proposal recommended
