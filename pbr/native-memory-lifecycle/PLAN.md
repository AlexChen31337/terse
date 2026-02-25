# PLAN: ADR-007 — Native Memory Lifecycle

**Status:** Ready for Builder  
**Date:** 2026-02-25  
**ADR:** `docs/architecture/ADR-007-native-memory-lifecycle.md`

---

## 1. Current Config State

```
memorySearch:  { "enabled": false }
compaction:    { "mode": "default" }
contextPruning: { "mode": "cache-ttl", "ttl": "1h" }
```

**Summary:** memorySearch is off, compaction has no memoryFlush, contextPruning is already partially enabled (cache-ttl, 1h).

---

## 2. Exact config.patch Payload

Three separate `config.patch` calls (order matters — do them sequentially):

### Patch 1: Enable memorySearch

```json
{
  "agents": {
    "defaults": {
      "memorySearch": {
        "enabled": true,
        "sources": ["memory", "sessions"],
        "extraPaths": ["~/.openclaw/workspace/memory"],
        "provider": "local",
        "store": {
          "driver": "sqlite",
          "path": "~/.openclaw/memory.db",
          "vector": { "enabled": true }
        },
        "query": {
          "maxResults": 10,
          "minScore": 0.3,
          "hybrid": {
            "enabled": true,
            "vectorWeight": 0.6,
            "textWeight": 0.4,
            "temporalDecay": { "enabled": true, "halfLifeDays": 30 }
          }
        },
        "sync": {
          "onSessionStart": true,
          "onSearch": true,
          "watch": true,
          "watchDebounceMs": 5000,
          "intervalMinutes": 30,
          "sessions": { "deltaMessages": 10 }
        },
        "chunking": { "tokens": 512, "overlap": 64 }
      }
    }
  }
}
```

### Patch 2: Enable compaction memoryFlush

```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "mode": "safeguard",
        "reserveTokens": 8000,
        "keepRecentTokens": 4000,
        "memoryFlush": {
          "enabled": true,
          "softThresholdTokens": 150000,
          "prompt": "Extract and save the most important facts, decisions, project status, and lessons from this conversation to memory. Focus on what future-me will need to know.",
          "systemPrompt": "You are saving important context to long-term memory before conversation compaction. Be concise but complete."
        }
      }
    }
  }
}
```

### Patch 3: Update contextPruning (extend TTL, add tool deny list)

```json
{
  "agents": {
    "defaults": {
      "contextPruning": {
        "mode": "cache-ttl",
        "ttl": "2h",
        "keepLastAssistants": 10,
        "softTrimRatio": 0.3,
        "hardClearRatio": 0.15,
        "minPrunableToolChars": 2000,
        "tools": {
          "deny": ["Read", "exec"]
        }
      }
    }
  }
}
```

### Post-patch verification

```bash
openclaw doctor 2>&1 | grep -E "error|warning|unknown" | head -5
openclaw config get agents.defaults.memorySearch 2>&1 | head -20
openclaw config get agents.defaults.compaction 2>&1 | head -20
openclaw config get agents.defaults.contextPruning 2>&1 | head -10
```

---

## 3. sqlite-vec Availability

**✅ Available.** Found at:
```
~/.local/share/fnm/node-versions/v22.22.0/installation/lib/node_modules/openclaw/node_modules/sqlite-vec-linux-x64/vec0.so
```

Bundled with OpenClaw itself — no separate install needed. `vector.enabled: true` will work.

**Fallback (if vec0 fails to load at runtime):** Patch `vector.enabled` to `false`. FTS5 text search still works. Apply:
```json
{ "agents": { "defaults": { "memorySearch": { "store": { "vector": { "enabled": false } } } } } }
```

---

## 4. AGENTS.md Changes

### 4a. REMOVE entire section: "Memory Retrieval Protocol (MANDATORY)"

Remove from `## Memory Retrieval Protocol (MANDATORY)` through the end of `### Integration with Existing Memory Files:` (inclusive of the "Your workflow:" block). This is lines starting with:

```
## Memory Retrieval Protocol (MANDATORY)

**⚠️ CRITICAL: Before answering ANY question, you MUST search tiered memory for relevant context.**
```

Through and including:

```
**Your workflow:**
1. Write to `memory/YYYY-MM-DD.md` for new events (raw notes)
2. Search tiered memory for past context (tree retrieval)
3. Update `MEMORY.md` for critical lessons (manual curation)
```

### 4b. REPLACE with simplified section:

```markdown
## Memory

You wake up fresh each session. These files are your continuity:
- **Daily notes:** `memory/YYYY-MM-DD.md` (create `memory/` if needed) — raw logs of what happened
- **Long-term:** `MEMORY.md` — your curated memories

**Native memory search is automatic.** OpenClaw indexes your memory files and injects relevant context on session start and before every search. You don't need to call any scripts manually.

**Your workflow:**
1. Write to `memory/YYYY-MM-DD.md` for new events (raw notes)
2. Update `MEMORY.md` for critical lessons (manual curation)
3. Trust that native search surfaces relevant past context automatically
```

### 4c. In the existing `## Memory` section (just below "Memory Retrieval Protocol"), REMOVE the duplicate memory description

The current `## Memory` section says:
```
## Memory

You wake up fresh each session. These files are your continuity:
- **Daily notes:** `memory/YYYY-MM-DD.md` (create `memory/` if needed) — raw logs of what happened
- **Long-term:** `MEMORY.md` — your curated memories, like a human's long-term memory
- **Tiered memory:** Searchable via tree index — use `memory_cli.py retrieve` before answering

Capture what matters. Decisions, context, things to remember. Skip the secrets unless asked to keep them.
```

**Replace** with the simplified text from 4b above (merging into one section — don't have two Memory sections).

### 4d. In `### 🧠 MEMORY.md - Your Long-Term Memory` — keep as-is (no changes needed)

### 4e. In `### 📝 Write It Down - No "Mental Notes"!` — keep as-is (no changes needed)

---

## 5. HEARTBEAT.md Changes

### 5a. REMOVE entire section: "Session Wake Detection"

Remove from `## Session Wake Detection (ALWAYS RUN FIRST — every heartbeat)` through the line:
```
3. If SAME session: continue to other checks below.
```

This removes all `check_new_session.sh`, `memory_cli.py retrieve`, `hybrid_cli.py search`, and `update_session_id.py` references.

**No replacement needed** — session detection is now handled natively by `memorySearch.sync.onSessionStart`.

### 5b. REMOVE entire section: "Hybrid Memory Reindex"

Remove from `## Hybrid Memory Reindex (every 12 hours)` through:
```
3. Update lastHybridMemoryReindex timestamp in memory/heartbeat-state.json
```

**No replacement needed** — native `sync.watch` + `sync.intervalMinutes: 30` handles reindexing.

### 5c. KEEP: RSI Loop Health and Simmer sections — unchanged.

### Final HEARTBEAT.md should contain only:
1. `## RSI Loop Health (every 4+ hours)` — unchanged
2. `## Simmer Prediction Markets (every 4+ hours)` — unchanged

---

## 6. SOUL.md Changes

### 6a. In `## Core Truths`, REMOVE:

```
**Search First, Answer Second.** Before answering ANY question, search tiered memory. This is non-negotiable. WAL misses happen when I skip this step. AGENTS.md protocol: `uv run python skills/tiered-memory/scripts/memory_cli.py retrieve --query "<key terms>" --limit 5`
```

**Replace with:**

```
**Memory is automatic now.** Native OpenClaw memory search indexes and injects relevant context on session start and before searches. No manual retrieval scripts needed. Just write to daily notes and trust the system.
```

### 6b. No other SOUL.md changes needed.

---

## 7. Archive Plan

### 7a. Create archive directory and move skills

```bash
mkdir -p skills/archived
mv skills/tiered-memory skills/archived/tiered-memory
mv skills/hybrid-memory skills/archived/hybrid-memory
mv skills/session-guard skills/archived/session-guard
```

### 7b. Add README to archived directory

Create `skills/archived/README.md`:
```markdown
# Archived Skills

These skills were deprecated by ADR-007 (2026-02-25) in favour of native OpenClaw lifecycle primitives.

- **tiered-memory** → replaced by `agents.defaults.memorySearch`
- **hybrid-memory** → replaced by `agents.defaults.memorySearch` (hybrid query)
- **session-guard** → replaced by `agents.defaults.contextPruning` + `compaction.memoryFlush`

To restore: move the skill directory back to `skills/` and revert the config changes.
```

### 7c. Remove cron jobs referencing deprecated skills

Check and remove any crons that call tiered-memory or hybrid-memory scripts:
```bash
openclaw cron list 2>&1 | grep -i -E "tiered|hybrid|session.guard|memory_cli|hybrid_cli|check_new_session"
```
Delete any matching cron entries.

### 7d. Update memory/heartbeat-state.json

Remove `lastHybridMemoryReindex` key if present (no longer tracked).

---

## 8. Verification Steps

After all changes are applied:

### 8a. Config verification
```bash
openclaw config get agents.defaults.memorySearch.enabled  # expect: true
openclaw config get agents.defaults.compaction.mode        # expect: "safeguard"
openclaw config get agents.defaults.compaction.memoryFlush.enabled  # expect: true
openclaw config get agents.defaults.contextPruning.ttl     # expect: "2h"
```

### 8b. Restart gateway and check logs
```bash
openclaw gateway restart
sleep 5
openclaw gateway status 2>&1 | head -20
# Check for memory-related startup messages
journalctl --user -u openclaw -n 50 --no-pager 2>/dev/null | grep -i -E "memory|vector|sqlite|index" | head -10
```

### 8c. Functional test — new session memory injection
1. Start a new session (or restart gateway)
2. Ask a question about something only in `memory/` files (e.g., a past decision)
3. Verify the answer includes context from memory WITHOUT any manual `memory_cli.py` call
4. Check that `~/.openclaw/memory.db` exists and has data:
```bash
ls -la ~/.openclaw/memory.db
```

### 8d. Verify archived skills don't break anything
```bash
# Confirm skills are gone from active directory
ls skills/tiered-memory 2>&1  # should fail
ls skills/hybrid-memory 2>&1  # should fail
ls skills/session-guard 2>&1  # should fail
# Confirm they're in archive
ls skills/archived/tiered-memory skills/archived/hybrid-memory skills/archived/session-guard
```

### 8e. Doctor check
```bash
openclaw doctor 2>&1 | head -20
```

---

## 9. Rollback Plan

If native memory breaks (no injection, crashes, or bloated context):

### Quick rollback (< 2 min)
```bash
# Disable native memory
openclaw config patch '{"agents":{"defaults":{"memorySearch":{"enabled":false},"compaction":{"mode":"default","memoryFlush":{"enabled":false}},"contextPruning":{"mode":"cache-ttl","ttl":"1h"}}}}'

# Restore skills
mv skills/archived/tiered-memory skills/tiered-memory
mv skills/archived/hybrid-memory skills/hybrid-memory
mv skills/archived/session-guard skills/session-guard

# Restart
openclaw gateway restart
```

### Full rollback (< 10 min)
1. Run quick rollback above
2. `git checkout -- AGENTS.md HEARTBEAT.md SOUL.md` (revert file changes)
3. Re-create any deleted cron jobs from git history
4. Verify with `openclaw doctor`

### Pre-change safety
Before the Builder starts, take a snapshot:
```bash
cd /home/bowen/.openclaw/workspace
git add -A && git commit -m "pre-ADR-007: snapshot before native memory migration"
openclaw config get agents.defaults > /tmp/pre-adr007-config.json
```

---

## Execution Order for Builder

1. **Snapshot** current state (git commit + config backup)
2. **Apply Patch 1** (memorySearch) → verify
3. **Apply Patch 2** (compaction/memoryFlush) → verify
4. **Apply Patch 3** (contextPruning update) → verify
5. **Run `openclaw doctor`** → confirm clean
6. **Edit AGENTS.md** per §4
7. **Edit HEARTBEAT.md** per §5
8. **Edit SOUL.md** per §6
9. **Archive skills** per §7
10. **Remove deprecated cron jobs** per §7c
11. **Restart gateway** → verify
12. **Run verification steps** per §8
13. **Git commit** all changes: `"ADR-007: migrate to native OpenClaw memory lifecycle"`
