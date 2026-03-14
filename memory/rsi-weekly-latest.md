# RSI Weekly Report — 2026-03-15

## Executive Summary
- **Health Score:** 0.134 (CRITICAL — below 0.3 threshold)
- **Outcomes Analyzed:** 148 (7-day window)
- **Success Rate:** 31%
- **Avg Quality:** 2.16/5
- **Patterns Detected:** 4
- **Proposals Generated:** 4 (all previously deployed)
- **Critical Alerts:** ✅ Health score < 0.3 — ALERT REQUIRED

---

## Top Failure Patterns

### 🔴 Pattern #1: tool_error (Severity: 1.236)
- **Context:** `tool_call` tasks
- **Frequency:** 61 occurrences
- **Failure Rate:** 100%
- **Status:** Repair proposals already deployed

### 🟡 Pattern #2: context_loss (Severity: 0.622)
- **Context:** `session_management` tasks
- **Frequency:** 46 occurrences
- **Failure Rate:** 0% (non-fatal but degrading)
- **Status:** Repair proposals already deployed

### 🟡 Pattern #3: tool_validation_error (Severity: 0.568)
- **Context:** `tool_call` tasks
- **Frequency:** 21 occurrences
- **Failure Rate:** 100%
- **Status:** Repair proposals already deployed

---

## Proposals Status
- **Previously Deployed:** 4 proposals (all auto-approved)
- **New Proposals:** 0 (all patterns already addressed)
- **Awaiting Review:** 0

---

## Health Trend
⚠️ **CRITICAL** — Health score 0.134 is well below the 0.3 threshold. This indicates systemic issues with tool reliability and session management. The 31% success rate over 7 days is concerning and needs attention.

---

## Recommended Actions
1. **URGENT:** Investigate tool_error pattern — 61/61 failures in tool_call tasks
2. Review context_loss mitigation — 46 instances in session_management
3. Audit tool_validation pipeline — 21/21 failures indicate validation logic issues

Generated: 2026-03-15 03:00 AEDT
