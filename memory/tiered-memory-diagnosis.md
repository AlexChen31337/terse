# Tiered Memory System Health Diagnosis
**Date:** 2026-02-16 00:18 AEDT  
**Triggered by:** Failed to find "ship faster repo" in memory search

## 🚨 Issues Found

### 1. **CRITICAL: Semantic Search Disabled**

**Symptom:** `memory_search` tool returns error:
```
No API key found for provider "openai"
No API key found for provider "google"  
No API key found for provider "voyage"
```

**Root cause:** Tiered memory system requires embedding API for semantic search. We have:
- ✅ Google OAuth (Antigravity, Gemini CLI)
- ❌ OpenAI API key
- ❌ Google AI Studio API key (text-embedding-004)
- ❌ Voyage AI API key

**Impact:**
- `memory_search` tool completely disabled
- Falls back to keyword search (`memory_cli.py retrieve`)
- Keyword search has poor recall ("ship faster repo" didn't match "ship-faster")
- I should have used grep as fallback but gave up too early

**Evidence:**
```bash
# Failed search
memory_search("ship faster repo") → error, no results

# Manual keyword search found it
memory_cli.py retrieve --query "artifact approval gates runs"
→ Found: "Analyzed ship-faster repo: artifact-first execution..."
```

### 2. **CRITICAL: Tree Node Counts Are Wrong**

**Symptom:** Tree shows inflated memory counts:
```
📁 general — Memories: warm=259, cold=0  (actual: 20)
📁 projects/evoclaw — Memories: warm=153, cold=0  (actual: 55)
📁 technical/gpu — Memories: warm=250, cold=0  (actual: 48)
```

**Actual counts:**
```python
Total facts: 163 (correct)
projects/evoclaw: 55
technical/gpu: 48
general: 20
```

**Root cause:** Tree counting logic is double/triple counting facts, possibly counting subcategories multiple times.

**Impact:**
- Misleading tree visualization
- Can't trust tree for capacity planning
- May trigger incorrect evictions if based on tree counts

### 3. **MAJOR: Warm Memory Over Capacity**

**Symptom:**
- Config limit: 50KB
- Actual size: 59KB (18% over)
- Fact count: 163

**Root cause:** No recent consolidation enforcement.

**Impact:**
- Slower searches (linear scan of 163 items)
- Higher context cost when loading warm memory
- Eviction should have triggered at 50KB

### 4. **MINOR: Timestamp Corruption in Consolidation**

**Symptom:**
```json
"last_consolidation": 38960871080.17382
```

This timestamp is invalid (year 3204 if interpreted as seconds).

**Root cause:** Bug in consolidation timestamp recording.

**Impact:**
- Metrics unreliable for "time since last consolidation"
- May skip consolidation checks thinking it's recent

### 5. **MINOR: No Embedding Metadata**

**Symptom:** Ship-faster entry has empty metadata:
```json
"metadata": {
  "urls": [],
  "commands": [],
  "paths": ["/tasks/context", "/transfers/deploys"]  // Wrong extraction
}
```

**Expected:** Should have extracted:
- `urls`: ["https://github.com/bowen31337/ship-faster"]
- `paths`: ["runs/", "proposal.md", "tasks.md", "context.json"]

**Root cause:** Metadata extraction regex doesn't match all URL formats.

**Impact:**
- Can't search by URL
- Missing structured data for retrieval

## 🔍 Why I "Forgot" Ship-Faster Repo

**Chain of failures:**

1. User asked: "What we can adopt from ship faster repo"
2. I ran: `memory_search("ship faster repo")`
3. Tool failed: No embedding API key configured
4. I should have: Run `grep -r "ship" memory/*.json` or `memory_cli.py retrieve`
5. Instead: Assumed it wasn't stored, asked user for URL
6. User (correctly) called me out: "Check your memory, tiered system should have it"

**The ship-faster entry WAS stored** (at 00:14:54):
```json
{
  "id": "e93af2630e0f",
  "text": "Analyzed ship-faster repo: artifact-first execution...",
  "category": "projects/evoclaw/architecture",
  "created_at": 1771161294.243141,
  "tier": "warm"
}
```

**But keyword search failed because:**
- Query: "ship faster repo"
- Stored text: "ship-faster repo" (hyphenated)
- Keyword overlap: only "repo" matched (weak signal)
- Better query: "artifact approval gates" (found immediately)

## 🛠️ Fixes Required

### Fix 1: Enable Semantic Search (High Priority)

**Option A: Use existing Google AI Studio access**
```bash
# Get API key from Google AI Studio
# https://aistudio.google.com/app/apikey

# Add to OpenClaw config
openclaw configure --section memory
# Prompt will ask for embedding provider + key
```

**Option B: Use local embeddings (Ollama)**
```bash
# Use ollama with nomic-embed-text
ollama pull nomic-embed-text

# Update tiered memory config to use local embeddings
# (requires skill modification)
```

**Option C: Hybrid approach**
```bash
# Add fallback to grep when semantic search fails
# Update memory_search tool to:
# 1. Try semantic search
# 2. If no API key, fall back to memory_cli.py retrieve
# 3. If still no results, fall back to grep
```

**Recommendation:** Option C (graceful degradation) + Option A (proper fix)

### Fix 2: Fix Tree Node Counting (High Priority)

**Location:** `skills/tiered-memory/scripts/memory_cli.py`

**Bug:** Tree counting likely in `TreeIndex._update_memory_counts()`

**Fix approach:**
1. Count facts directly per category (don't sum children)
2. Parent nodes should show sum of children + own facts
3. Add test to verify counts match actual warm-memory.json

**Test:**
```python
# After fix, verify:
tree_count = tree.get_node("projects/evoclaw").memory_count
actual_count = len([f for f in warm_facts if f['category'].startswith('projects/evoclaw')])
assert tree_count == actual_count
```

### Fix 3: Enforce Warm Memory Capacity (Medium Priority)

**Current:** 59KB / 50KB limit (no enforcement)

**Fix options:**

A. **Run consolidation now**
```bash
cd ~/clawd
python3 skills/tiered-memory/scripts/memory_cli.py consolidate --mode daily
```

B. **Auto-evict on store**
```python
# In WarmMemory.store():
if self.get_size_kb() > self.config['max_kb']:
    self.evict_lowest_scored(target_kb=self.config['max_kb'] * 0.9)
```

C. **Add to heartbeat checks**
```bash
# In HEARTBEAT.md
if memory size > 50KB:
  Run consolidation
```

**Recommendation:** A (immediate) + B (long-term) + C (monitoring)

### Fix 4: Fix Consolidation Timestamp (Low Priority)

**Location:** `skills/tiered-memory/scripts/memory_cli.py` in `consolidate()`

**Bug:** Writing wrong timestamp format

**Fix:**
```python
# Replace
metrics['last_consolidation'] = datetime.now().timestamp()

# With
metrics['last_consolidation'] = int(time.time())
```

### Fix 5: Improve Metadata Extraction (Low Priority)

**Current regex misses:**
- `https://github.com/user/repo` (extracts as path `/transfers/deploys`)
- `github.com/user/repo` (no https://)

**Fix:** Update URL regex in metadata extraction:
```python
# Add to patterns
r'(?:https?://)?github\.com/[\w-]+/[\w-]+',
r'(?:https?://)?(?:www\.)?[a-z0-9-]+\.[a-z]{2,}(?:/\S*)?',
```

### Fix 6: Add Graceful Degradation to memory_search Tool (High Priority)

**Current behavior:**
```
memory_search fails → return error → agent gives up
```

**Desired behavior:**
```
memory_search fails → fall back to keyword search → fall back to grep → return partial results with warning
```

**Implementation location:** OpenClaw agent's `memory_search` tool wrapper

**Pseudocode:**
```python
def memory_search(query, max_results=5):
    # Try semantic search first
    try:
        results = semantic_search(query)
        if results:
            return results
    except NoAPIKeyError:
        pass  # Fall through
    
    # Fall back to keyword search
    try:
        results = exec("memory_cli.py retrieve --query '{query}'")
        if results:
            return {"results": results, "method": "keyword", "warning": "Semantic search unavailable"}
    except:
        pass
    
    # Last resort: grep
    results = exec("grep -i '{query}' memory/*.json memory/*.md")
    return {"results": results, "method": "grep", "warning": "Limited search quality"}
```

## 📋 Action Plan

### Immediate (Today)

- [x] Diagnose why ship-faster wasn't found
- [ ] Run consolidation to enforce 50KB limit
- [ ] Add grep fallback when memory_search fails

### Short-term (This Week)

- [ ] Get Google AI Studio API key for embeddings
- [ ] Configure tiered memory to use semantic search
- [ ] Fix tree node counting bug
- [ ] Test retrieval with 10+ queries

### Medium-term (Next Sprint)

- [ ] Add auto-eviction on warm memory overflow
- [ ] Fix timestamp corruption bug
- [ ] Improve URL/metadata extraction
- [ ] Add memory health check to heartbeat

### Long-term (Future)

- [ ] Benchmark keyword vs semantic search quality
- [ ] Consider local embeddings (Ollama) for offline operation
- [ ] Add memory compaction (deduplicate similar facts)

## 📊 Current Health Score: 6/10

**Working:**
- ✅ Storage (writes succeed)
- ✅ Hot memory (under limit, clean structure)
- ✅ Keyword search (when you use right terms)
- ✅ Daily notes ingestion

**Broken:**
- ❌ Semantic search (disabled)
- ❌ Tree node counts (inflated)
- ❌ Capacity enforcement (over limit)
- ⚠️ Metadata extraction (incomplete)
- ⚠️ Consolidation tracking (corrupted timestamp)

**Impact on agent performance:**
- Can't find memories without exact keyword match
- High false-negative rate on searches
- Misleading tree visualization
- Slower retrieval (oversized warm memory)

**Why it still works:**
- Daily notes cover short-term context
- Hot memory covers core identity
- MEMORY.md covers long-term (manual curation)
- Grep still works as last resort

**But:** Without semantic search, tiered memory is 50% as effective as designed.

---

**Recommendation:** Prioritize semantic search API key (30 min fix, 10x impact).
