# Memory Retrieval Protocol - Hardened Behavior Rules

**Date:** 2026-02-17 10:57 AM AEDT
**Requested by:** Bowen Li
**Implemented by:** Alex Chen

## Request

"Harden openclaw behaviour rules that always search tiered memory nodes via page index approach and find related information context before answering the question"

## Changes Made

### 1. Added Mandatory Memory Retrieval Section to AGENTS.md

**Location:** After "Every Session", before "Memory" section

**New Protocol:**
```markdown
## Memory Retrieval Protocol (MANDATORY)

Before answering ANY question, you MUST search tiered memory for relevant context.

Standard Retrieval Flow:
1. Parse the question
2. Search tiered memory using tree-based page index
3. Review retrieved nodes (1-3KB context)
4. Synthesize answer with memory + current knowledge
5. If no relevant memory → proceed with current knowledge
```

**Key Points:**
- Searches using `memory_cli.py retrieve` command
- Tree-based navigation (O(log n), not O(n) scan)
- LLM-powered reasoning, not vector similarity
- Explicit "when to search" guidelines
- Integration with existing daily notes workflow

### 2. Updated MEMORY.md Critical Lessons

**Added:**
```
[memory] Always search tiered memory via tree index before answering questions — Bowen explicit
[workflow] Memory retrieval is mandatory, not optional — use page index approach
```

### 3. Updated Memory Section in AGENTS.md

**Before:**
- Daily notes, MEMORY.md only

**After:**
- Daily notes, MEMORY.md, **and tiered memory**
- Explicit mention: "use `memory_cli.py retrieve` before answering"

## Why This Matters

### Problem Before:
1. **Memory retrieval was optional** — agent could answer without checking past context
2. **No standard workflow** — inconsistent use of tiered memory
3. **Context loss** — answers lacked historical perspective
4. **Violated tiered memory design** — system exists but wasn't being used systematically

### Solution After:
1. **Mandatory retrieval** — hardcoded into workflow
2. **Clear process** — 5-step protocol
3. **Better answers** — grounded in actual past events
4. **Utilizes existing infrastructure** — tiered memory system fully leveraged

## Example Usage

**User:** "How's the LTX-2 setup going?"

**Old behavior (wrong):**
```
Check current state → answer based on what I can see now
```

**New behavior (correct):**
```bash
# Step 1: Search memory
python3 skills/tiered-memory/scripts/memory_cli.py retrieve "LTX-2 setup" --limit 5

# Step 2: Review results
Found: "LTX-2 FP8 models downloaded (27GB checkpoint, Gemma 3 23GB...)"
Found: "Temporal upscaler download in progress (25% at 09:30)..."

# Step 3: Synthesize answer
"Based on memory: LTX-2 FP8 checkpoint (27GB) and Gemma 3 (23GB) are downloaded.
Temporal upscaler was 25% complete at 9:30 AM, likely finished by now.
Let me verify current status..."
```

## Integration with Existing Systems

### Tiered Memory Architecture:
```
Tree Index (2KB)
    ↓ LLM-powered search
Warm Memory (50KB)
    ↓ Retrieved nodes (1-3KB)
Agent Response
```

### Daily Workflow:
1. **Write:** Log to `memory/YYYY-MM-DD.md`
2. **Search:** Query tiered memory via tree index
3. **Consolidate:** Automatic ingestion during cron jobs
4. **Curate:** Update MEMORY.md with critical lessons

### No Changes Required to:
- Daily note format
- Consolidation jobs
- Cloud sync
- Tree index structure

## Verification

To test this works:

```bash
# Ask a question that should trigger memory search
"What did we work on yesterday?"

# Expected behavior:
# 1. Agent runs: memory_cli.py retrieve "yesterday work" --limit 5
# 2. Retrieves relevant nodes from warm memory
# 3. Synthesizes answer with context
# 4. Shows reasoning: "Based on memory from 2026-02-16..."
```

## Benefits

1. **Consistency** — every agent session uses same retrieval protocol
2. **Context continuity** — past decisions inform current answers
3. **Reduced hallucination** — grounded in actual events, not assumptions
4. **Better UX** — "I remember when we..." vs "I don't have that info"
5. **Full utilization** — tiered memory system not underused anymore

## Follow-up

- [ ] Monitor memory retrieval usage in practice
- [ ] Add metrics: % of questions triggering retrieval
- [ ] Optimize tree index for common query patterns
- [ ] Consider caching frequent retrievals in hot memory

---

**Status:** ✅ Implemented and documented
**Files Modified:**
- `AGENTS.md` — Added mandatory retrieval protocol
- `MEMORY.md` — Added critical lessons
- `memory/2026-02-17-memory-retrieval-protocol.md` — This document

**Commit Message:**
```
feat(memory): enforce mandatory tiered memory retrieval before answering

- Add Memory Retrieval Protocol section to AGENTS.md
- Make tree-based search mandatory workflow step
- Update MEMORY.md with new critical lessons
- Document 5-step retrieval flow
- Integration with existing daily notes system

Requested by: Bowen Li
Implements: Tree-based page index approach for all questions
```
