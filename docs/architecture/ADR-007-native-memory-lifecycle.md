# ADR-007: Replace Skill-Based Memory with Native OpenClaw Lifecycle Primitives

**Status:** Proposed  
**Date:** 2026-02-25  
**Author:** Alex Chen  
**Refs:** session-guard skill, tiered-memory skill, hybrid-memory skill, RSI loop skill

---

## Context

Memory issues recur because the current architecture is **agent-cooperative**: tiered memory, session guard, and WAL all depend on the agent *remembering* to call them. Session resets wipe that memory, creating a circular dependency — the thing that fixes memory loss requires memory to invoke.

Current failure modes:
- Session reset → agent forgets to rehydrate → answers from stale knowledge
- Compaction approaches → WAL flush never fires → context lost permanently  
- Heartbeat misses → tiered memory never indexes → search returns nothing
- Python subprocess overhead → agents skip retrieval under token pressure

---

## Discovery: OpenClaw Already Has These Primitives

After reviewing the full config schema, OpenClaw ships with exactly what we need:

| Problem | OpenClaw Native Feature |
|---------|------------------------|
| Auto-rehydrate on session start | `memorySearch.sync.onSessionStart: true` |
| Auto-index file changes | `memorySearch.sync.watch: true` |
| Flush memory before compaction | `compaction.memoryFlush.enabled: true` |
| Prevent context explosion | `contextPruning.mode: cache-ttl` |
| Hybrid vector+text search | `memorySearch.query.hybrid.enabled: true` |
| SQLite vector store | `memorySearch.store.driver: sqlite` + `vector.enabled: true` |

We've been building Python wrappers around capabilities OpenClaw already provides at the runtime level.

---

## Decision

**Replace skill-based memory with native OpenClaw config.** Specifically:

### 1. Enable Native Memory Search (replaces tiered-memory + hybrid-memory)

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

**Effect:** On every session start, OpenClaw auto-indexes `memory/` files and injects relevant context. File watcher syncs new daily notes within 5s. No agent cooperation required.

### 2. Enable Memory Flush Before Compaction (replaces WAL pre-compaction step)

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

**Effect:** When context hits 150k tokens, OpenClaw automatically runs a memory extraction pass and saves to the memory store before compacting. Never silently loses context again.

### 3. Enable Context Pruning (replaces session-guard size monitoring)

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

**Effect:** Tool results older than 2h are pruned from context automatically. Prevents session bloat without agent monitoring itself.

---

## Consequences

### What gets deprecated
- `skills/tiered-memory/` — replaced by native memorySearch + SQLite vector store
- `skills/hybrid-memory/` — replaced by native hybrid query config  
- `skills/session-guard/` — replaced by native contextPruning + memoryFlush
- `check_new_session.sh` + `update_session_id.py` in HEARTBEAT.md — no longer needed
- Manual `memory_cli.py retrieve` calls from AGENTS.md — replaced by automatic injection

### What stays
- **RSI Loop** — remains as cron; it's about task outcome analysis, not lifecycle
- **Daily memory notes** (`memory/YYYY-MM-DD.md`) — still written by agent; native watcher picks them up automatically
- **MEMORY.md** — still curated manually; auto-indexed by file watcher
- **WAL for corrections** — still useful for within-session durability

### What gets simpler
- AGENTS.md drops the mandatory "search tiered memory before every answer" instruction
- HEARTBEAT.md drops session detection and hybrid memory reindex sections  
- New sessions just work — no startup ritual required

---

## Implementation Plan

**Phase 1 (config change, 30 min):**
1. Enable `memorySearch` with local SQLite vector store
2. Enable `compaction.memoryFlush`
3. Enable `contextPruning`
4. Test: create new session, verify memory auto-injects without manual retrieval

**Phase 2 (cleanup, 1-2h):**  
1. Update AGENTS.md — remove manual retrieval protocol
2. Update HEARTBEAT.md — remove session detection + hybrid memory sections
3. Archive (don't delete) tiered-memory, hybrid-memory, session-guard skills
4. Update SOUL.md — remove "NEVER skip memory search" and `uv run python memory_cli.py` references

**Phase 3 (validation, ongoing):**  
1. Monitor: does memory actually inject relevant context automatically?
2. Monitor: does memoryFlush fire before compaction? What does it save?
3. Tune: adjust vectorWeight, minScore, halfLifeDays based on retrieval quality

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Local vector model slow on startup | Medium | `provider: local` downloads once, caches; or use `provider: openai` |
| Memory injection bloats context | Low | `maxResults: 10` cap; `minScore: 0.3` filters noise |
| memoryFlush prompt loses nuance | Low | Prompt is configurable; review output on first fire |
| sqlite-vec extension not installed | Medium | Fallback: `vector.enabled: false` uses FTS5 only |

---

## Alternatives Considered

**A) Build custom OpenClaw plugin (Go/JS)**  
Rejected — OpenClaw's plugin API doesn't expose session lifecycle hooks. Would require forking OpenClaw.

**B) Keep Python skills, make crons more robust**  
Rejected — doesn't solve the circular dependency. Better crons still require agent cooperation on session start.

**C) Hybrid: native + Python scripts**  
Partial adoption — keep RSI loop (unique capability), drop the rest.

---

## Action Items

- [ ] `config.patch` to enable memorySearch + memoryFlush + contextPruning
- [ ] Verify sqlite-vec extension available at correct path
- [ ] Update AGENTS.md, HEARTBEAT.md, SOUL.md
- [ ] Archive deprecated skills
- [ ] 1-week monitoring period before declaring success
