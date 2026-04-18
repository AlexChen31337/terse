# Archived Skills

Deprecated by ADR-007 (2026-02-25) — replaced by native OpenClaw lifecycle primitives.

| Skill | Replaced by |
|-------|------------|
| tiered-memory | `agents.defaults.memorySearch` (SQLite vector + hybrid FTS5) |
| hybrid-memory | `agents.defaults.memorySearch.query.hybrid` |
| session-guard | `agents.defaults.contextPruning` + `compaction.memoryFlush` |

## Rollback
Move skill directories back to `skills/` and apply config rollback:
`openclaw config patch '{"agents":{"defaults":{"memorySearch":{"enabled":false},"compaction":{"mode":"default"}}}}'`
