# Skill Installation Protocol

**Hard rule:** Skills are **infrastructure**, not guidance. Installation = integration.

---

## What Skills Must Do On Installation

Every skill MUST provide an `install.sh` script that:

### 1. Auto-Configure Agent Files

**Required updates:**

#### SOUL.md
- Add skill-specific behavioral rules to "Lessons learned" or "Hard rules"
- Update "Self-Evolution Principles" if the skill enables new capabilities
- Example: `intelligent-router` adds "Always classify before spawning"

#### AGENTS.md
- Add usage protocol sections (e.g., "Sub-Agent Spawning Protocol")
- Document workflows and integration points
- Example: `tiered-memory` adds "Memory Consolidation" section

#### TOOLS.md (if applicable)
- Add tool-specific configuration (API keys, endpoints, device names)
- Example: GPU server specs, SSH hosts, service ports

### 2. Create Wrapper Scripts

If the skill requires repeated CLI usage, create wrapper scripts:
- Auto-load credentials from `memory/encrypted/`
- Auto-detect and inject environment variables
- Provide simplified commands (e.g., `memory consolidate` instead of `python3 memory_cli.py consolidate --db-url ... --auth-token ...`)

**Examples:**
- `tiered-memory`: Created `skills/tiered-memory/scripts/memory` wrapper
- `intelligent-router`: Created `skills/intelligent-router/scripts/spawn_helper.py`

### 3. Set Up Cron Jobs (if applicable)

Skills that need periodic execution MUST create cron jobs:
- Use `cron add` via OpenClaw API
- Document job IDs in skill metadata
- Example: `tiered-memory` creates 3 cron jobs (quick/daily/monthly consolidation)

### 4. Configure Dependencies

**Hard rule: Always use `uv` for Python dependencies.**

```bash
# Install dependencies
uv pip install -r requirements.txt

# Execute scripts
uv run python3 script.py

# NO pip, NO venv, NO exceptions
```

### 5. Validate Installation

Before completing, run health checks:
- Verify all files created
- Test wrapper scripts
- Validate cron jobs scheduled
- Check that SOUL.md/AGENTS.md were updated

**Output installation report:**
```
✅ Skill installed: tiered-memory v2.2.0
✅ Updated SOUL.md (added lesson)
✅ Updated AGENTS.md (added consolidation protocol)
✅ Created wrapper: skills/tiered-memory/scripts/memory
✅ Created cron jobs: 3 (quick/daily/monthly)
✅ Dependencies installed via uv
✅ Health check passed
```

---

## Installation Script Template

```bash
#!/usr/bin/env bash
# install.sh - Auto-configure skill infrastructure

set -euo pipefail

SKILL_NAME="your-skill"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"

echo "🔧 Installing $SKILL_NAME..."

# 1. Install Python dependencies (if any)
if [[ -f "$SKILL_DIR/requirements.txt" ]]; then
    echo "📦 Installing dependencies via uv..."
    uv pip install -r "$SKILL_DIR/requirements.txt"
fi

# 2. Update SOUL.md
echo "📝 Updating SOUL.md..."
SOUL_FILE="$WORKSPACE_ROOT/SOUL.md"
if ! grep -q "your-skill-specific-lesson" "$SOUL_FILE"; then
    # Insert lesson before the "Philosophy:" section
    sed -i '/^\*\*Philosophy:\*\*/i - **Your lesson** — Your lesson text' "$SOUL_FILE"
fi

# 3. Update AGENTS.md
echo "📝 Updating AGENTS.md..."
AGENTS_FILE="$WORKSPACE_ROOT/AGENTS.md"
if ! grep -q "## Your Skill Protocol" "$AGENTS_FILE"; then
    cat >> "$AGENTS_FILE" <<'EOF'

## Your Skill Protocol

Usage instructions here...
EOF
fi

# 4. Create wrapper scripts
echo "🔨 Creating wrapper scripts..."
cat > "$SKILL_DIR/scripts/wrapper" <<'EOF'
#!/usr/bin/env bash
# Auto-configured wrapper for your-skill
exec uv run python3 "$(dirname "$0")/main.py" "$@"
EOF
chmod +x "$SKILL_DIR/scripts/wrapper"

# 5. Create cron jobs (example)
echo "⏰ Creating cron jobs..."
# Use OpenClaw cron API via sessions_send or direct API call
# Example: openclaw cron add --name "Your Job" --schedule ...

# 6. Validate
echo "✅ Validating installation..."
if [[ ! -f "$SKILL_DIR/scripts/wrapper" ]]; then
    echo "❌ Wrapper script not created"
    exit 1
fi

echo "✅ $SKILL_NAME installed successfully"
echo "✅ Updated SOUL.md"
echo "✅ Updated AGENTS.md"
echo "✅ Created wrapper scripts"
echo "✅ Health check passed"
```

---

## Retroactive Fixes for Existing Skills

For skills already installed (like `tiered-memory`, `intelligent-router`, `agent-self-governance`):

1. **Create `install.sh`** in each skill directory
2. **Document what was manually configured** (so install.sh can automate it)
3. **Add to skill metadata:**
   ```json
   {
     "auto_configured": true,
     "updated_files": ["SOUL.md", "AGENTS.md"],
     "created_wrappers": ["scripts/memory"],
     "cron_jobs": ["7e14b958-4593-4979-81a3-7fe89efcd29b"]
   }
   ```

---

## Testing Installation

After creating `install.sh`, test it:

```bash
# Fresh clone scenario
cd /tmp
git clone <workspace-repo> test-workspace
cd test-workspace
skills/your-skill/install.sh

# Verify:
# - SOUL.md updated
# - AGENTS.md updated
# - Wrapper scripts created
# - Cron jobs created
# - Health checks pass
```

---

## Why This Matters

**Before (guidance-only):**
- Skills provide docs, user reads and manually integrates
- Error-prone, inconsistent, documentation drift
- Every new OpenClaw user must manually configure

**After (infrastructure):**
- Skills self-install and self-configure
- Consistent across all agents
- Zero-config experience for new users
- Version-controlled integration

**Example:** When another OpenClaw user installs `tiered-memory`:
1. Runs `skills/tiered-memory/install.sh`
2. SOUL.md auto-updated with memory lessons
3. AGENTS.md auto-updated with consolidation protocol
4. Wrapper script created
5. Cron jobs scheduled
6. **Ready to use immediately**

---

**Hard rule:** Skills that don't provide `install.sh` are incomplete.

— Alex Chen, February 16 2026
