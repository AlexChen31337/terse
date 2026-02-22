# Unified Skill Specification

**Version:** 1.0.0  
**Status:** Canonical  
**Audience:** ClawHub, OpenClaw, EvoClaw runtimes

---

## Overview

The Unified Skill Specification defines a single skill package format that works across:

| Runtime | Reads | Ignores |
|---------|-------|---------|
| **OpenClaw** | `SKILL.md` (agent guidance), `scripts/` | `[genome]` section of skill.toml |
| **EvoClaw** | `SKILL.md` frontmatter (identity/perms), `[tools.*]` in `skill.toml` | Markdown body of SKILL.md |
| **ClawHub** | `skill.toml` (index + search), `SKILL.md` (display) | nothing |

---

## Directory Layout

```
skill-name/
├── SKILL.md               # Human-readable docs + YAML frontmatter (required)
├── skill.toml             # Machine manifest (required)
├── scripts/               # Python scripts (required if tools are defined)
│   └── main.py
├── tests/                 # Validation tests (required per ClawInfra standards)
│   └── test_skill.py
├── references/            # Optional: API docs, examples, cheat sheets
│   └── api-ref.md
└── pyproject.toml         # Optional: if skill needs a venv
```

> **No `bin/` directory.** EvoClaw invokes Python scripts via `uv run python` — no compiled
> binaries or wrappers needed.

---

## 1. SKILL.md

### Role

- **OpenClaw**: Primary agent guidance. Loaded into agent context. The agent reads this to know
  when and how to use the skill.
- **EvoClaw**: The YAML frontmatter is parsed to populate the `SkillManifest` struct (name,
  version, description, author, metadata.evoclaw).
- **ClawHub**: Displayed as the skill's documentation page.

### Frontmatter Schema

```yaml
---
name: skill-name                   # required, matches [skill].name in skill.toml
version: 1.0.0                     # required, semver
description: "One-line summary"    # required
author: "Name <email@example.com>" # required
license: MIT                       # optional, default MIT

# EvoClaw-specific metadata (read by EvoClaw Loader → SkillManifest.Metadata.EvoClaw)
metadata:
  evoclaw:
    permissions:                   # system-level permissions this skill needs
      - network                    # outbound HTTP/TCP
      - filesystem                 # file read/write beyond workspace
      - shell                      # subprocess execution
    env:                           # required environment variables (agent must have these)
      - ETHERSCAN_API_KEY
      - SOME_SECRET

# OpenClaw hint (optional — helps OpenClaw surface this skill)
tags: [crypto, trading, onchan]    # same as skill.toml [skill.tags]
---
```

### Body

The markdown body is free-form documentation for the agent. Follow this recommended structure:

```markdown
# Skill Name — Agent Skill

Short description.

## When to Use
- Trigger phrases / conditions
- Automatic triggers (heartbeat, signal thresholds)

## Quick Start
Shell commands or Python snippets the agent can copy-paste.

## Commands / Tools
Per-tool documentation.

## Output Format
JSON schema of tool outputs.

## Integration Pattern
Python snippet for calling from agent code.

## Configuration
Environment variables, config files.
```

---

## 2. skill.toml

### Role

- **ClawHub**: Primary index source. Used for search, install, version management.
- **EvoClaw**: `[tools.*]` sections are loaded by `ParseToolsTOML` and exposed to the agent as
  callable tools.  `[genome]` section drives evolutionary parameter bounds.
- **OpenClaw**: Ignored at runtime (OpenClaw reads `SKILL.md`), but used by ClawHub during
  `clawhub install` to validate the package.

### Full Schema

```toml
# ─────────────────────────────────────────────────────────────────────────────
# [skill] — Core identity (required)
# ─────────────────────────────────────────────────────────────────────────────
[skill]
name        = "skill-name"          # unique slug, kebab-case
version     = "1.0.0"              # semver
description = "One-line summary"   # shown in clawhub search results
author      = "Name <email>"
license     = "MIT"
repository  = "https://github.com/clawinfra/skill-name"
homepage    = "https://clawhub.dev/skills/skill-name"

# ─────────────────────────────────────────────────────────────────────────────
# [skill.compat] — Runtime compatibility declaration (required)
# ─────────────────────────────────────────────────────────────────────────────
[skill.compat]
openclaw = true    # works in OpenClaw (agent reads SKILL.md)
evoclaw  = true    # works in EvoClaw (tools + genome enabled)
clawhub  = true    # publishable to ClawHub

# Minimum runtime versions (optional)
openclaw_min = "0.9.0"
evoclaw_min  = "0.3.0"

# ─────────────────────────────────────────────────────────────────────────────
# [skill.tags] — Categorisation (optional but recommended)
# ─────────────────────────────────────────────────────────────────────────────
[skill.tags]
tags = ["crypto", "trading", "onchain"]

# ─────────────────────────────────────────────────────────────────────────────
# [skill.deps] — Runtime dependencies (optional)
# ─────────────────────────────────────────────────────────────────────────────
[skill.deps]
python   = ">=3.11"            # minimum Python version
packages = ["whalecli>=1.0"]   # pip/uv packages to install

# ─────────────────────────────────────────────────────────────────────────────
# [skill.evoclaw] — EvoClaw-specific metadata (required if evoclaw = true)
# Mirrors metadata.evoclaw in SKILL.md frontmatter — must stay in sync.
# ─────────────────────────────────────────────────────────────────────────────
[skill.evoclaw]
permissions = ["network"]         # same as SKILL.md metadata.evoclaw.permissions
env         = ["ETHERSCAN_API_KEY"]   # required env vars

# ─────────────────────────────────────────────────────────────────────────────
# [tools.*] — Tool definitions (required for EvoClaw; optional for OpenClaw-only)
#
# These sections are parsed by EvoClaw's ParseToolsTOML.  Each [tools.NAME]
# exposes one callable tool to the agent.  OpenClaw ignores these sections.
#
# Command execution: `uv run python` is the standard invoker for Python scripts.
# ─────────────────────────────────────────────────────────────────────────────
[tools.scan]
command     = "uv run python scripts/main.py scan"
description = "Run a one-shot analysis and return JSON results"
args        = ["--chain", "ETH", "--hours", "24"]    # default args
env         = ["ETHERSCAN_API_KEY"]
timeout_secs = 60

[tools.check]
command     = "uv run python scripts/main.py check"
description = "Quick signal check — returns BULLISH/BEARISH/NEUTRAL"
timeout_secs = 30

[tools.stream]
command     = "uv run python scripts/main.py stream"
description = "Stream real-time alerts as JSONL"
timeout_secs = 3600

# ─────────────────────────────────────────────────────────────────────────────
# [genome] — Evolutionary parameters (optional, EvoClaw only)
#
# OpenClaw completely ignores this section.
#
# Each parameter under [genome.params] defines a scalar value EvoClaw can
# mutate.  The bounds (min/max) constrain the mutation search space.
# The 'value' key is the default / current value.
#
# Supported types: "int", "float", "bool"
#
# EvoClaw maps these into SkillGenome.Params and evolves them per evaluation
# cycle.  The bridge adapter reads these when building a SkillGenome JSON
# for direct genome injection.
# ─────────────────────────────────────────────────────────────────────────────
[genome]
weight = 0.7        # default SkillGenome.Weight (0.0-1.0)
enabled = true      # default SkillGenome.Enabled

[genome.params]
# key = { value = default, min = lower_bound, max = upper_bound, type = "..." }
scan_hours        = { value = 24,  min = 1,  max = 168, type = "int"   }
score_threshold   = { value = 70,  min = 40, max = 95,  type = "int"   }
alert_threshold   = { value = 75,  min = 50, max = 95,  type = "int"   }
poll_interval_secs = { value = 60, min = 30, max = 3600, type = "int"  }
```

---

## 3. Scripts

### Invocation Convention

All scripts MUST be invocable with:

```bash
uv run python scripts/<name>.py <subcommand> [args...]
```

EvoClaw uses the `command` field from `[tools.NAME]` verbatim. No binary wrappers, no compiled
artifacts. The `uv run` prefix handles the venv automatically.

### Script Standards

- Full `argparse` with subcommands
- Return **JSON to stdout** on success
- Return **error JSON to stderr** + non-zero exit on failure
- Exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | No results (ran OK, nothing to report) |
| 2 | External API / auth error |
| 3 | Network / connectivity error |
| 4 | Data / input validation error |
| 5 | Internal unexpected error |

- Type-annotated (`from __future__ import annotations`)
- Passes `mypy --strict`

---

## 4. Compatibility Declarations

The `[skill.compat]` table tells ClawHub how to present and install the skill:

```toml
# OpenClaw-only skill (no tool defs needed, no genome section)
[skill.compat]
openclaw = true
evoclaw  = false
clawhub  = true

# EvoClaw-only skill (SKILL.md needed for manifest parsing)
[skill.compat]
openclaw = false
evoclaw  = true
clawhub  = true

# Universal skill (tools + SKILL.md body both present)
[skill.compat]
openclaw = true
evoclaw  = true
clawhub  = true
```

ClawHub uses this to:
- Show/hide "Install for OpenClaw" / "Install for EvoClaw" buttons
- Validate that required sections exist (`[tools.*]` if evoclaw=true)
- Route `clawhub install` to the right install path

---

## 5. Runtime Consumption

### OpenClaw

1. `clawhub install <skill>` — downloads package, places in `skills/<name>/`
2. Agent reads `SKILL.md` body at session start (added to context)
3. Agent invokes scripts via `exec(["uv", "run", "python", "scripts/..."])` as needed

### EvoClaw

1. `clawhub install <skill>` OR `evoclaw skill install <skill>` — downloads package, places in
   `~/.evoclaw/skills/<name>/`
2. `Loader.loadSkill()` reads:
   - `SKILL.md` frontmatter → `SkillManifest`
   - `skill.toml` `[tools.*]` sections → `map[string]*ToolDef` (via `ParseToolsTOML`)
3. `GenerateSchemas()` converts `ToolDef` → LLM-compatible tool schema
4. Agent calls tools by name; executor runs `command` with `args`, captures stdout/stderr
5. Evolution engine reads `[genome.params]` to set mutation bounds on `SkillGenome.Params`

### Bridge Adapter

The `skill-bridge` skill provides CLI tooling to convert between formats and install across
runtimes. See [Bridge Adapter](#bridge-adapter) below.

---

## 6. ClawHub Publishing

Unchanged from current flow. `clawhub publish` packages the entire skill directory. The registry
now additionally:

1. Validates `skill.toml` exists and is parseable
2. Indexes `[skill]`, `[skill.compat]`, `[skill.tags]`
3. Displays `SKILL.md` body as the skill page
4. Shows compat badges (OpenClaw / EvoClaw / Both)

---

## 7. Bridge Adapter

The `skill-bridge` skill provides:

```
bridge.py convert-to-evoclaw <skill-dir>   # SKILL.md → skill.toml (EvoClaw-ready)
bridge.py convert-to-openclaw <skill-dir>  # skill.toml → SKILL.md (OpenClaw-ready)
bridge.py validate <skill-dir>             # Check both formats present and consistent
bridge.py install-evoclaw <skill-dir> <evoclaw-skills-dir>
                                           # Copy + create agent.toml from [tools.*]
```

Location: `skills/skill-bridge/scripts/bridge.py`

---

## 8. Migration Guide

### Migrating an OpenClaw-only skill

1. Add `skill.toml` with `[skill]`, `[skill.compat]` (openclaw=true, evoclaw=false), `[skill.tags]`
2. If you want EvoClaw support: add `[tools.*]` sections + `[skill.evoclaw]` + update SKILL.md frontmatter
3. Run `bridge.py validate .` — fix any inconsistencies

### Migrating an EvoClaw-only skill

1. Add/update `SKILL.md` with full frontmatter (name, version, description, author, metadata.evoclaw)
2. Write a proper markdown body so OpenClaw agents can understand the skill
3. Add `[skill.compat]` to `skill.toml`
4. Run `bridge.py validate .`

---

## 9. Design Rationale

| Decision | Rationale |
|----------|-----------|
| SKILL.md stays primary for OpenClaw | OpenClaw injects docs into agent context; TOML not human-readable enough |
| skill.toml stays primary for EvoClaw | ParseToolsTOML already understands this format; `agent.toml` was just a naming convention |
| `uv run python` instead of binaries | No compilation step; works on all platforms; venv handled automatically |
| `[genome.params]` in skill.toml | Keeps evolutionary config co-located with tool definitions; OpenClaw silently ignores it |
| Compat table explicit | Avoids implicit detection; author declares intent |
| Tools optional for OpenClaw | Many OpenClaw skills are docs-only (LSP guides, references) |
| Bridge generates `agent.toml` | Backward-compatible; existing EvoClaw Loader unchanged |
