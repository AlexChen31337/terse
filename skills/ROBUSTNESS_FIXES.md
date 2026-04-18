# Skills Robustness Fixes - 2026-02-12

## Summary

Fixed 6 critical robustness issues in intelligent-router and tiered-memory skills to make them production-ready for EvoClaw integration.

---

## ✅ Intelligent Router Fixes

### 1. Fallback Model Selection ✅
**Issue:** `recommend_model()` only returned primary model, ignored fallback in routing_rules  
**Fix:** Updated to return both primary and fallback models, with optional `use_fallback` parameter  
**Impact:** Router can now gracefully fall back if primary model fails or is unavailable

**Code changes:**
- Modified `recommend_model()` to check routing_rules for primary/fallback
- Returns dict with `model` (primary) and `fallback` keys
- Added `use_fallback` param to swap them if needed

**Test:**
```bash
cd ~/clawd/skills/intelligent-router
python3 scripts/router.py classify "fix lint errors"
# Returns: primary=DeepSeek V3.2, fallback=Llama 3.3 70B
```

---

## ✅ Tiered Memory Fixes

### 2. Atomic File Writes ✅
**Issue:** File writes not atomic — corruption risk if process killed during write  
**Fix:** Implemented `atomic_write_json()` using temp file + rename pattern  
**Impact:** All JSON writes now atomic (warm, hot, tree, metrics)

**Code changes:**
- Added `atomic_write_json()` function
- Updated `WarmMemory.save()`, `HotMemory.save()`, `MemoryTree.save()`, `save_metrics()`
- Uses `tempfile.NamedTemporaryFile()` + `shutil.move()` for atomic rename

### 3. Schema Versioning ✅
**Issue:** No version field in JSON files — can't detect incompatible formats  
**Fix:** Added `SCHEMA_VERSION = "2.0"` and `load_json_with_version()`  
**Impact:** Future schema changes won't break old memory files

**Code changes:**
- Constant `SCHEMA_VERSION = "2.0"` at top of file
- `atomic_write_json()` adds `_schema_version` to dicts
- `load_json_with_version()` checks version and warns if incompatible

### 4. Agent ID Sanitization ✅
**Issue:** `agent_id` not validated — path traversal attack possible (`../../../etc`)  
**Fix:** Added `sanitize_agent_id()` validation  
**Impact:** Prevents malicious agent_id from accessing files outside memory/

**Code changes:**
- Function `sanitize_agent_id()` strips path separators, validates alphanumeric
- `get_agent_paths()` now calls sanitize before building paths
- Raises `ValueError` if invalid chars detected

### 5. Turso Connection Pooling ✅
**Issue:** New DB connection per call — hits rate limits, slow  
**Fix:** Simple connection pool with 5min TTL  
**Impact:** Reuses connections, reduces latency and rate limit errors

**Code changes:**
- Global `_turso_pool` dict with conn/last_used/ttl
- `get_turso_connection()` reuses if <TTL old, creates new if stale
- Pool invalidated on error

### 6. Retry Logic with Exponential Backoff ✅
**Issue:** Transient Turso errors caused immediate failure  
**Fix:** `turso_execute_with_retry()` with 3 retries, exponential backoff  
**Impact:** Resilient to transient network/DB issues

**Code changes:**
- Function `turso_execute_with_retry()` wraps Turso calls
- Retries up to 3 times with 1s, 2s, 4s backoff
- Invalidates pool connection on error

---

## Files Modified

1. `skills/intelligent-router/scripts/router.py`
   - Line 102-124: Updated `recommend_model()` with fallback support

2. `skills/tiered-memory/scripts/memory_cli.py`
   - Lines 81-203: Added security/robustness functions
   - Line 640: Updated `WarmMemory.save()` to use atomic write
   - Line 451: Updated `HotMemory.save()` to use atomic write
   - Line 278: Updated `MemoryTree.save()` to use atomic write
   - Line 1419: Updated `save_metrics()` to use atomic write
   - Line 207: Updated `get_agent_paths()` to sanitize agent_id

---

## Testing

### Intelligent Router
```bash
cd ~/clawd/skills/intelligent-router
python3 scripts/router.py health
# Status: HEALTHY ✅

python3 scripts/router.py classify "fix lint errors in utils.js"
# Returns primary + fallback correctly ✅
```

### Tiered Memory
```bash
cd ~/clawd
python3 skills/tiered-memory/scripts/memory_cli.py store \
  --text "Test robustness" --category "testing" --agent-id "test-agent"
# {"id": "...", "tier": "warm", ...} ✅

# Verify atomic write created file
cat memory/test-agent/warm-memory.json
# File created successfully ✅

# Verify agent_id sanitization
python3 skills/tiered-memory/scripts/memory_cli.py store \
  --text "Evil" --category "test" --agent-id "../../../etc/passwd"
# ValueError: Invalid agent_id ✅
```

---

## Remaining Issues (Not Critical)

### P1 (High Priority - Future)
- Add logging support to router (--log-file flag)
- Transaction rollback for memory consolidation
- LLM timeout in distiller (30s default)
- Unit tests for both skills (Pytest with 80%+ coverage)

### P2 (Medium Priority)
- Cost caps and warnings in router
- Pagination for large Turso queries
- Tree search indexing (O(log n) instead of O(n))

### P3 (Low Priority)
- JSON Schema validation for configs
- Hot memory checksums
- Model availability health checks

---

## EvoClaw Integration Readiness

✅ **READY** - Both skills now meet minimum production standards:

- ✅ Multi-agent support (tiered-memory)
- ✅ Zero external deps (intelligent-router)
- ✅ Atomic file operations
- ✅ Input sanitization
- ✅ Schema versioning
- ✅ Connection pooling
- ✅ Retry logic
- ✅ Graceful degradation (fallback models)

**Recommendation:** Safe to integrate into EvoClaw. Monitor logs for any edge cases.

---

**Fixed by:** Alex Chen  
**Date:** 2026-02-12 12:30 AEDT  
**Audit doc:** `/tmp/skills-robustness-audit.md`
