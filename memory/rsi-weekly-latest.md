# RSI Weekly Report
**Date:** 2026-03-28 16:00 UTC
**Cycle:** 7 days

## Executive Summary
- **Health Score:** 0.104 (CRITICAL — < 0.3 threshold)
- **Outcomes Logged:** 250 (7d)
- **Success Rate:** 25%
- **Avg Quality:** 2.09/5

## Top Failure Patterns
1. **tool_error** (75 occurrences) — 100% failure rate in `tool_call` tasks
2. **timeout** (73 occurrences) — 100% failure rate in `tool_call` tasks
3. **context_loss** (62 occurrences) — session restart/compaction issues

## Proposals Status
- **Draft:** 1 proposal awaiting review
  - `3b8e8f52`: Address `incomplete_task` in `message_routing` tasks (2 occurrences)
- **Deployed:** 24 proposals (all previous fixes already applied)
- **Rejected:** 3 proposals

## Prevention Rules in Place
✅ All critical patterns have prevention rules in `HEARTBEAT.md`:
- `context_loss` → WAL + active_task.py protocol
- `tool_validation_error` → angle-bracket formatting ban + param checks
- `tool_error` → claude_agent_sdk mock rule for claw_forge tests

## Pending Action Required
**NEW:** Draft proposal `3b8e8f52` needs review:
- **Priority:** Critical
- **Issue:** `message_routing` tasks failing with `incomplete_task` (2x, 100% failure)
- **Est. Effort:** 30 minutes
- **Action:** Investigate message routing failures and document fix in AGENTS.md

## Alert Threshold
Health score 0.104 < 0.3 → **Alert recommended to Bowen**

**Recommendation:** Review draft proposal `3b8e8f52` and approve deployment if valid.
