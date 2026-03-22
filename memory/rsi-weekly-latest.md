# RSI Weekly Report
**Generated:** 2026-03-22 03:00 AEDT (2026-03-21 16:00 UTC)
**Analysis Period:** 7 days (162 outcomes logged)

---

## Health Score: 0.155 / 1.0 ⚠️

**Status:** Critical - Immediate action required
**Overall Success Rate:** 35%
**Average Quality:** 2.24/5

---

## Top Failure Patterns (7 days)

### 1. [0.963 severity] Timeout in tool_call tasks
- **Occurrences:** 52
- **Failure Rate:** 100%
- **Impact:** CRITICAL - Tasks failing entirely due to timeouts

### 2. [0.704 severity] Tool errors in tool_call tasks
- **Occurrences:** 38
- **Failure Rate:** 100%
- **Impact:** HIGH - Tools failing during execution

### 3. [0.679 severity] Context loss in session_management
- **Occurrences:** 55
- **Failure Rate:** 0%
- **Impact:** MEDIUM - Degraded performance but tasks complete

---

## Issue Breakdown (7 days)

| Issue Type | Count | % of Total |
|------------|-------|------------|
| context_loss | 55 | 34% |
| timeout | 52 | 32% |
| tool_error | 38 | 23% |
| Other | 17 | 11% |

**Total:** 162 logged outcomes

---

## Proposals Generated

This cycle generated 5 proposals, all previously deployed:
- db32089a (already deployed)
- b9e26a71 (already deployed)
- 60126e7f (already deployed)
- 15c31c37 (already deployed)
- 84a2e40b (already deployed)

**Auto-deployed this cycle:** 0
**Total deployed all-time:** 24

---

## Recommendations

### IMMEDIATE (Today)
1. **Investigate timeout root cause** - 52 timeout failures in tool_call tasks is unacceptable
   - Check which tools are timing out
   - Review timeout configurations
   - Consider increasing timeouts or fixing slow operations

2. **Fix tool_error cascade** - 38 tool errors suggest brittle error handling
   - Audit recent tool changes
   - Add defensive wrappers around unreliable tools
   - Implement retry logic for transient failures

3. **Context loss mitigation** - 55 occurrences suggests memory/compaction issues
   - Verify WAL is working correctly
   - Check compaction settings
   - Ensure active_task.py is being used for multi-step work

### SHORT-TERM (This Week)
- Review the 5 deployed proposals to verify they're actually working
- Consider running RSI cycle daily until health score > 0.5
- Audit tool_call patterns for systemic issues

---

## Next Actions

```bash
# Run daily cycle until health improves
uv run python skills/rsi-loop/scripts/rsi_cli.py cycle --days 1

# Check specific tool errors
uv run python skills/rsi-loop/scripts/rsi_cli.py patterns

# View proposals
ls skills/rsi-loop/data/proposals/
```

---

**Report stored at:** `memory/rsi-weekly-latest.md`
**Next scheduled:** 2026-03-29 03:00 AEDT
