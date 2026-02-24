# RSI Loop Health Check Report
**Generated:** 2026-02-24 03:02 AM AEDT

---

## 🚨 CRITICAL ALERT

**Health Score: 0.176 / 1.0** (WELL BELOW 0.3 THRESHOLD)

---

## Metrics Summary

| Metric | Value | Status |
|--------|-------|--------|
| Health Score | 0.176 | 🔴 CRITICAL |
| Outcomes (24h) | 23 | ✅ OK |
| Outcomes (7d) | 68 total | - |
| Success Rate | 35% | 🔴 POOR |
| Avg Quality | 2.5/5 | 🔴 POOR |
| Test Results | 32 passed | ✅ PASS |
| Pending Proposals | 21 files | ⚠️ HIGH |

---

## Top Failure Patterns

1. **[0.794 confidence]** `none` in 'unknown' tasks — **78% failure rate** (18 occurrences)
2. **[0.603 confidence]** `tool_error` in 'unknown' tasks — **100% failure** (13 occurrences)
3. **[0.338 confidence]** `wal_miss` in 'unknown' tasks — **100% failure** (7 occurrences)

---

## Recent Issues (Last 7 Days)

- **tool_error:** 17 occurrences
- **wal_miss:** 11 occurrences
- **context_loss:** 9 occurrences

---

## Proposals Status

### Awaiting Deployment (3 ready):
- `2cea18f8`: Fix wal_miss in memory_retrieval tasks
- `56638f19`: Fix tool_error in infrastructure_ops tasks
- `fcc33a1d`: Address 'none' in 'unknown' tasks

### Newly Generated (5 proposals from this cycle):
- `[682e6962]` Address 'tool_error' in 'unknown' tasks
- `[8479eda7]` Address 'wal_miss' in 'unknown' tasks
- `[c98028aa]` Address 'cost_overrun' in 'trading' tasks
- `[f4533796]` Address 'wal_miss' in 'trading' tasks
- `[1d3f9b39]` Address 'tool_error' in 'trading' tasks

---

## Test Results
✅ **ALL TESTS PASSED** (32/32 in 0.68s)

---

## 🔔 Immediate Action Required

The health score of **0.176** is critically low. Bowen should review:

1. **Why are 78% of 'unknown' tasks failing with 'none'?** — This suggests tasks aren't being classified properly
2. **Tool errors are spiking** — 17 occurrences in 7 days
3. **WAL misses remain high** — 11 occurrences, indicating memory retrieval protocol isn't being followed

---

*Report saved to memory/rsi-healthcheck-latest.md*
