---
name: skill-bridge
version: 1.0.0
description: "Unified Skill Spec bridge adapter — convert, validate, and install skills across OpenClaw and EvoClaw runtimes."
author: "Alex Chen <alex.chen31337@gmail.com>"
license: MIT
tags: [devtools, skills, evoclaw, openclaw, clawhub]
metadata:
  evoclaw:
    permissions:
      - filesystem
      - shell
    env: []
---

# skill-bridge — Agent Skill

Convert and install skills between OpenClaw and EvoClaw formats.
Implements the [Unified Skill Specification](../../docs/architecture/unified-skill-spec.md).

## When to Use

- "Convert this skill for EvoClaw"
- "Add skill.toml to this OpenClaw skill"
- "Install whalecli into my EvoClaw agent"
- "Validate that skill-bridge uses the unified format"
- "Check if a skill is compatible with both runtimes"
- Any time you add or modify a skill and want to keep both formats in sync

## Quick Start

```bash
# Validate a skill directory
uv run python skills/skill-bridge/scripts/bridge.py validate skills/whalecli

# Add EvoClaw support to an OpenClaw-only skill
uv run python skills/skill-bridge/scripts/bridge.py convert-to-evoclaw skills/my-skill

# Generate SKILL.md from an existing skill.toml
uv run python skills/skill-bridge/scripts/bridge.py convert-to-openclaw skills/my-skill

# Install a skill into a local EvoClaw agent
uv run python skills/skill-bridge/scripts/bridge.py install-evoclaw \
    skills/whalecli ~/.evoclaw/skills
```

## Commands

### `validate <skill-dir>`

Checks that a skill directory is valid for both runtimes:
- `SKILL.md` is present with required frontmatter (name, version, description)
- `skill.toml` is present and parseable
- Name and version are consistent between the two files
- `[tools.*]` sections have required fields (command)
- `[genome.params]` bounds are valid (min ≤ value ≤ max)
- `scripts/` and `tests/` directories exist

**Exit codes:**
- `0` — valid
- `1` — errors found (stdout shows details)

### `convert-to-evoclaw <skill-dir>`

Reads `SKILL.md` frontmatter and generates a `skill.toml` with:
- `[skill]` metadata from frontmatter
- `[skill.compat]` set to `openclaw=true, evoclaw=true`
- `[tools.*]` stubs for each `.py` file in `scripts/`
- `[genome]` scaffold with empty params

Use after creating a new OpenClaw skill that you want to also run on EvoClaw.
You'll need to fill in the tool `description` and `command` fields.

### `convert-to-openclaw <skill-dir>`

Reads `skill.toml` and generates/updates `SKILL.md`:
- If `SKILL.md` exists: updates frontmatter (name, version, author, tags, evoclaw metadata)
- If `SKILL.md` is missing: generates a full template

Use after receiving an EvoClaw-native skill that needs OpenClaw documentation.

### `install-evoclaw <skill-dir> <evoclaw-skills-dir>`

Copies a skill into EvoClaw's skills directory and creates the files EvoClaw needs:

1. Validates the skill (fails fast on errors)
2. Copies the directory to `<evoclaw-skills-dir>/<skill-name>/`
3. Generates `agent.toml` from `[tools.*]` sections in `skill.toml`
4. Generates `genome.json` if the skill has `[genome.params]`

```bash
# Install into local EvoClaw agent
uv run python skills/skill-bridge/scripts/bridge.py install-evoclaw \
    skills/whalecli ~/.evoclaw/skills

# Install into a specific EvoClaw instance
uv run python skills/skill-bridge/scripts/bridge.py install-evoclaw \
    skills/fear-harvester /path/to/evoclaw-instance/skills
```

## Unified Skill Format Reference

A fully unified skill directory looks like:

```
skill-name/
├── SKILL.md        ← OpenClaw reads this (agent guidance + frontmatter)
├── skill.toml      ← EvoClaw + ClawHub reads this (tools + genome params)
├── scripts/
│   └── main.py     ← invoked by both runtimes via `uv run python`
└── tests/
    └── test_main.py
```

**SKILL.md frontmatter** declares identity and EvoClaw permissions:
```yaml
---
name: my-skill
version: 1.0.0
description: "What it does"
author: "Name <email>"
metadata:
  evoclaw:
    permissions: [network]
    env: [MY_API_KEY]
---
```

**skill.toml** declares tools and evolutionary parameters:
```toml
[skill]
name    = "my-skill"
version = "1.0.0"

[skill.compat]
openclaw = true
evoclaw  = true

[tools.run]
command      = "uv run python scripts/main.py run"
description  = "Run the skill"
timeout_secs = 60

[genome]
weight = 0.6

[genome.params]
threshold = { value = 70, min = 40, max = 95, type = "int" }
```

## Integration Pattern

```python
import subprocess, json

def validate_skill(skill_dir: str) -> bool:
    result = subprocess.run(
        ["uv", "run", "python", "skills/skill-bridge/scripts/bridge.py",
         "validate", skill_dir],
        capture_output=True, text=True
    )
    print(result.stdout)
    return result.returncode == 0

def install_skill_evoclaw(skill_dir: str, evoclaw_skills_dir: str) -> None:
    subprocess.run(
        ["uv", "run", "python", "skills/skill-bridge/scripts/bridge.py",
         "install-evoclaw", skill_dir, evoclaw_skills_dir],
        check=True
    )
```

## Full Specification

See: `docs/architecture/unified-skill-spec.md`
