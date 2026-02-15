# EvoClaw PR Ready — February 16, 2026 09:15 AEDT

**Executed autonomously per Bowen's directive: "Go ahead"**

---

## Summary

**PR created:** `feat/core-skills-infrastructure`
**Location:** `/tmp/evoclaw/` (branch: `feat/core-skills-infrastructure`)
**Status:** ✅ READY FOR REVIEW

**What it does:** Adds 3 core skills as embedded infrastructure that auto-install during `evoclaw init`.

---

## Changes

### Core Skills Added (`/skills/`)

1. **tiered-memory v2.2.0**
   - Three-tier memory system (hot/warm/cold) with cloud sync
   - Auto-creates wrapper script with Turso credential loading
   - 2,134 lines of Python (memory_cli.py)

2. **intelligent-router v2.2.0**
   - Cost-optimized model routing (15-dimension weighted scoring)
   - Spawn helper for automatic classification
   - 721 lines of Python (router.py)

3. **agent-self-governance**
   - WAL, VBR, ADL, VFM protocols
   - 4 Python scripts (wal.py, vbr.py, adl.py, vfm.py)
   - Complements Go implementations in `internal/governance/`

### Templates Added (`/templates/`)

- **SOUL.md.template** - Agent persona with {{placeholders}}
  - Hard rules (uv for Python, core skills are infrastructure)
  - Self-governance protocol descriptions
  - Becomes ADL baseline for persona drift detection

- **AGENTS.md.template** - Behavioral rules
  - Memory management guide
  - Sub-agent spawning protocol
  - Safety guidelines

### Code Integration

**New: `internal/cli/skills_setup.go`**
- `SetupCoreSkills()` - Copies embedded skills, runs install.sh
- `GenerateAgentFiles()` - Generates SOUL.md/AGENTS.md from templates
- `copyEmbeddedDir()` - Recursively copies embedded directories

**Modified: `internal/cli/init.go`**
- Calls skill installation after config generation
- Non-fatal errors (warns but continues)

**New: `docs/SKILLS_INTEGRATION.md`**
- 513 lines of comprehensive documentation
- Architecture explanation
- Installation flow diagram
- Developer guide

**New: `PR_DESCRIPTION.md`**
- Detailed PR description with motivation
- Testing instructions
- Compatibility notes

---

## Statistics

```
36 files changed
11,158 lines added
0 lines deleted

Breakdown:
- tiered-memory: ~4,400 lines
- intelligent-router: ~1,800 lines
- agent-self-governance: ~800 lines
- Templates: ~200 lines
- Integration code: ~200 lines
- Documentation: ~4,000 lines
```

---

## Why This Matters

From EVOLUTION.md:

> "The genome is the soul. Evolution is the journey."

**The problem:** EvoClaw's evolution engine expects these skills but they weren't bundled.

**Evidence:**
- `internal/governance/adl.go` loads SOUL.md — but no template existed
- EVOLUTION.md references WAL for mutation logging — but skill wasn't installed
- VBR verification mentioned in docs — but script wasn't available

**The fix:** Bundle skills as embedded infrastructure, auto-install during init.

---

## Installation Flow (After This PR)

```
evoclaw init
│
├── Prompt for config (name, provider, API key)
├── Generate evoclaw.json
│
├── Install core skills: ✅ NEW
│   ├── tiered-memory → ~/.evoclaw/skills/tiered-memory/
│   ├── intelligent-router → ~/.evoclaw/skills/intelligent-router/
│   └── agent-self-governance → ~/.evoclaw/skills/agent-self-governance/
│
├── Generate agent files: ✅ NEW
│   ├── ~/.evoclaw/SOUL.md (from template)
│   └── ~/.evoclaw/AGENTS.md (from template)
│
└── Done → evoclaw start
```

---

## Testing Done

**Locally tested:**
```bash
cd /tmp/evoclaw
go build -o evoclaw ./cmd/evoclaw
./evoclaw init --non-interactive --provider ollama --name test-agent

# Verified:
✅ Skills copied to ~/.evoclaw/skills/
✅ install.sh scripts executed
✅ SOUL.md and AGENTS.md generated
✅ Health checks passed
```

**Skills verified working:**
```bash
~/.evoclaw/skills/tiered-memory/scripts/memory metrics
~/.evoclaw/skills/intelligent-router/scripts/router.py health
python3 ~/.evoclaw/skills/agent-self-governance/scripts/wal.py status default
```

---

## Next Steps

### For Bowen:

1. **Review the PR:**
   ```bash
   cd /tmp/evoclaw
   git log --oneline -3
   git show HEAD --stat
   cat PR_DESCRIPTION.md
   ```

2. **Test locally (optional):**
   ```bash
   cd /tmp/evoclaw
   go build -o evoclaw ./cmd/evoclaw
   ./evoclaw init
   ```

3. **Push to GitHub:**
   ```bash
   cd /tmp/evoclaw
   git remote add origin git@github.com:clawinfra/evoclaw.git
   git push origin feat/core-skills-infrastructure
   ```

4. **Create PR on GitHub:**
   - Use content from `PR_DESCRIPTION.md`
   - Link to EVOLUTION.md and SELF-GOVERNANCE.md
   - Request review from @clawinfra/core

### Post-Merge:

- Update ONBOARDING.md to mention core skills
- Add to CHANGELOG.md (if exists)
- Consider adding `evoclaw skills update` command
- Dashboard UI for skill management

---

## Commit Message

```
feat: Add core skills infrastructure integration

Adds three core skills as embedded infrastructure that auto-install during evoclaw init:

Core Skills:
- tiered-memory (v2.2.0): Three-tier memory system with cloud sync
- intelligent-router (v2.2.0): Cost-optimized model routing (15-dimension scoring)
- agent-self-governance: WAL/VBR/ADL/VFM reliability protocols

Templates:
- SOUL.md.template: Agent persona with self-governance lessons
- AGENTS.md.template: Behavioral rules and protocols

Integration:
- internal/cli/skills_setup.go: Copies embedded skills, runs install.sh
- internal/cli/init.go: Calls skill installation after config generation
- Skills auto-configure during init (zero-config experience)

Why These Are Core:
- WAL ensures genome mutations survive crashes (EVOLUTION.md)
- VBR verifies mutations before committing (EVOLUTION.md)
- ADL loads SOUL.md for persona baseline (internal/governance/adl.go)
- VFM scores mutation cost-effectiveness
- Tiered memory persists across evolution cycles
- Router enables cost-optimized fitness evaluation

Closes: #[issue] (evolution engine requires these skills to function)
Refs: EVOLUTION.md, docs/SELF-GOVERNANCE.md
```

---

## Files in PR

All files staged and committed:
- `/tmp/evoclaw/skills/` (3 skills, all scripts, configs, docs)
- `/tmp/evoclaw/templates/` (SOUL.md.template, AGENTS.md.template)
- `/tmp/evoclaw/internal/cli/skills_setup.go` (new)
- `/tmp/evoclaw/internal/cli/init.go` (modified)
- `/tmp/evoclaw/docs/SKILLS_INTEGRATION.md` (new)
- `/tmp/evoclaw/PR_DESCRIPTION.md` (new, for GitHub PR text)

---

**Autonomous execution complete.**  
**Time:** ~40 minutes  
**Status:** ✅ READY FOR REVIEW

— Alex Chen
