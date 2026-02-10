# Tiered Memory

Three-tier memory system (hot/warm/cold) for OpenClaw agents. Replaces growing MEMORY.md with a fixed-size hot tier, scored warm tier, and unlimited cloud archive.

**Version:** 1.3.0  
**License:** MIT

## Architecture

| Tier | Storage | Size | Purpose |
|------|---------|------|---------|
| 🔴 Hot | `MEMORY.md` | 4KB max | Always in context — core identity, active projects, key learnings |
| 🟡 Warm | `memory/warm-memory.json` | 50KB max | Scored recent facts with decay — auto-evicts lowest scored |
| 🟢 Cold | Turso (LibSQL) | Unlimited | Cloud archive — disaster recovery, long-term search |

## Quick Start

### 1. Install
```bash
clawhub install tiered-memory
```

### 2. Store a fact
```bash
python3 scripts/memory_cli.py store --text "Project X uses React 19" --category "projects/x" --importance 0.7
```

### 3. Search across tiers
```bash
python3 scripts/memory_cli.py retrieve --query "React project"
```

### 4. Run consolidation
```bash
python3 scripts/memory_cli.py consolidate
```

## Features

- **Exponential decay scoring** — recent facts score higher, old facts fade
- **Reinforcement** — frequently accessed facts get boosted
- **Hierarchical tree index** — category-based organization (50 nodes max)
- **Auto-eviction** — warm facts archive to cold after 2 days, hard-evict at 30 days
- **Cloud-first** — dual-write to Turso for disaster recovery
- **Hot state sync** — critical agent identity backed up to cloud
- **Zero external deps** — Python stdlib only

## CLI Commands

| Command | Description |
|---------|-------------|
| `store` | Store a fact in warm (+ optional cold dual-write) |
| `retrieve` | Search across all tiers |
| `consolidate` | Evict expired, archive to cold, rebuild hot |
| `stats` | Show tier sizes and usage |
| `tree` | View/manage category tree index |
| `warm` | List, search, or evict warm facts |
| `cold` | Init tables, store, or query cold storage |
| `rebuild-hot` | Regenerate MEMORY.md from tiers |
| `hot-state` | Update core identity (owner/agent/lessons/projects) |

## Cold Storage Setup (Optional)

Requires a [Turso](https://turso.tech) database:

```bash
# Initialize tables
python3 scripts/memory_cli.py cold --init --db-url "https://your-db.turso.io" --auth-token "your-token"

# Store with cloud dual-write
python3 scripts/memory_cli.py store --text "Important fact" --category "general" --db-url "..." --auth-token "..."

# Consolidate with cold archival
python3 scripts/memory_cli.py consolidate --db-url "..." --auth-token "..."
```

## Configuration

Key constants in `memory_cli.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `HOT_MAX_BYTES` | 4096 | Max MEMORY.md size |
| `WARM_MAX_KB` | 50 | Max warm tier size |
| `COLD_ARCHIVE_DAYS` | 2 | Archive to cold after N days |
| `WARM_RETENTION_DAYS` | 30 | Hard-evict from warm after N days |
| `HALF_LIFE_DAYS` | 30 | Score half-life for decay |
| `EVICTION_THRESHOLD` | 0.3 | Min score to survive eviction |

## How It Works

1. **Store** → fact goes to warm tier (+ cold if configured)
2. **Score** = importance × recency_decay × reinforcement
3. **Consolidate** → evicts low-score old facts, archives to cold, rebuilds MEMORY.md
4. **Retrieve** → searches tree index → warm → cold (cascading)
5. **Hot rebuild** → top 10 warm facts + hot state → MEMORY.md (kept under 4KB)
