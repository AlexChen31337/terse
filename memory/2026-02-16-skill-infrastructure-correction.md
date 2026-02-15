# Skill Infrastructure Correction — February 16, 2026 08:40 AEDT

**Bowen's correction:** "Consider those skills infrastructure not guidance"

**Second hard rule:** "Use uv for python installation and execute, no exception"

---

## What Changed

### Before (Wrong Approach)
- Skills were treated as **guidance** — docs + scripts that users read and integrate manually
- Installation = copy files, read SKILL.md, manually update SOUL.md/AGENTS.md/cron
- Inconsistent across agents, error-prone, documentation drift

### After (Correct Approach)
- Skills are **infrastructure** — self-installing, self-configuring
- Installation = run `install.sh`, everything auto-configured
- Consistent, zero-config for new users

---

## Hard Rules Added to SOUL.md

```markdown
**Hard rules (non-negotiable):**
- **Always use `uv` for Python** — Installation, execution, dependencies. No pip, no venv. No exceptions.
- **Skills are infrastructure** — Not guidance. They auto-configure SOUL.md, AGENTS.md, cron jobs, wrappers. Installation = integration.
```

---

## What Skills Must Do

Created `skills/SKILL-INSTALL-PROTOCOL.md` documenting:

### 1. Auto-Configure Agent Files
- Update SOUL.md with behavioral rules
- Update AGENTS.md with usage protocols
- Update TOOLS.md with tool-specific config

### 2. Create Wrapper Scripts
- Auto-load credentials
- Simplify CLI usage
- Example: `memory consolidate` instead of `python3 memory_cli.py consolidate --db-url ... --auth-token ...`

### 3. Set Up Cron Jobs
- Skills needing periodic execution create cron jobs automatically
- Example: `tiered-memory` creates 3 jobs (quick/daily/monthly)

### 4. Configure Dependencies
- **Always use `uv`** — No pip, no venv, no exceptions
- `uv pip install -r requirements.txt`
- `uv run python3 script.py`

### 5. Validate Installation
- Health checks before completion
- Installation report showing what was configured

---

## Retroactive Work Needed

**Existing skills to update:**
1. `tiered-memory` — Create `install.sh`
2. `intelligent-router` — Create `install.sh`
3. `agent-self-governance` — Create `install.sh`
4. All other skills in workspace

**Each `install.sh` must:**
- Install deps via `uv`
- Update SOUL.md with lessons
- Update AGENTS.md with protocols
- Create wrapper scripts
- Create cron jobs
- Validate installation
- Output report

---

## Example: How tiered-memory SHOULD Install

```bash
$ skills/tiered-memory/install.sh

🔧 Installing tiered-memory v2.2.0...
📦 Installing dependencies via uv...
📝 Updating SOUL.md... (added memory consolidation lesson)
📝 Updating AGENTS.md... (added Memory Consolidation section)
🔨 Creating wrapper scripts... (created scripts/memory)
⏰ Creating cron jobs... (created 3 jobs: quick/daily/monthly)
✅ Validating installation...
✅ tiered-memory installed successfully
✅ Updated SOUL.md
✅ Updated AGENTS.md  
✅ Created wrapper: scripts/memory
✅ Created 3 cron jobs
✅ Dependencies installed via uv
✅ Health check passed
```

**Result:** User can immediately run `memory consolidate` without any manual configuration.

---

## Why This Matters

**For new OpenClaw users:**
- Install skill → everything auto-configured
- No reading docs, no manual integration
- Consistent experience across all agents

**For skill developers:**
- Clear protocol to follow
- Installation = integration
- Versioned, reproducible

**For maintenance:**
- Update skill → run `install.sh` again → auto-updates SOUL.md/AGENTS.md
- No documentation drift
- Single source of truth

---

## Action Items

1. ✅ **Updated SOUL.md** — Added hard rules
2. ✅ **Logged to WAL** — Two correction entries
3. ✅ **Created protocol doc** — `skills/SKILL-INSTALL-PROTOCOL.md`
4. 🔲 **Create install.sh for tiered-memory**
5. 🔲 **Create install.sh for intelligent-router**
6. 🔲 **Create install.sh for agent-self-governance**
7. 🔲 **Test installation on fresh clone**

---

**Status:** Protocol documented, retroactive work queued.

— Alex Chen
