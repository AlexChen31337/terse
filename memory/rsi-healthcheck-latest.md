# RSI Loop Health Check — 2026-04-29

**Time:** 2026-04-29 03:10 AEST (2026-04-28 17:10 UTC)

## Pre-Cycle Status
- **Health Score:** 0.248 ⚠️ (below 0.3 threshold)
- **Outcomes (7d):** 97 logged | Success: 64% | Avg quality: 3.21/5
- **Top issues:** context_loss(62), tool_error(14), rate_limit(11)
- **Patterns:** 4 detected | Analyzed: 2026-04-27

## Post-Cycle Status
- **Health Score:** 0.41 (improved after cycle)
- **Patterns found:** 6
- **Proposals generated:** 5
- **Auto-deployed:** 0 (all already deployed or auto-approved)

## Active Auto-Fixes
- [b9e26a71] Address 'tool_error' in 'tool_call' tasks
- [3a2dc2d1] Fix model routing rate limits
- [15c31c37] Address 'tool_validation_error' in 'tool_call' tasks
- [db32089a] Address 'timeout' in 'tool_call' tasks

## Alert
⚠️ Pre-cycle health score 0.248 was below 0.3 threshold — alerting Bowen via Telegram.
