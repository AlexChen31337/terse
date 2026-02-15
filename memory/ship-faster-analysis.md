# Ship-Faster Analysis for EvoClaw/ClawChain
**Date:** 2026-02-16  
**Source:** https://github.com/bowen31337/ship-faster

## 🎯 What is Ship-Faster?

A **skill package system** for AI coding agents (Claude Code, Cursor, OpenCode) focused on:
- **Resumability** — Every workflow writes artifacts to disk (proposal.md, tasks.md, context.json, evidence/)
- **Auditability** — Full execution logs, approval gates before side effects
- **Composability** — Skills compose into workflows with predictable I/O contracts
- **Progressive disclosure** — Load details only when needed, not everything upfront

**Key insight:** Treat files as first-class citizens. Context is expensive, side effects are risky.

## 🏗️ Core Architecture Patterns

### 1. **Artifact-First Execution (Runs System)**

Every workflow creates a run directory:
```
runs/<workflow>/<run_id>/
  proposal.md       # What/why/scope (stable context)
  tasks.md          # [ ] → [x] checklist (resume here!)
  context.json      # Machine-readable switches
  evidence/         # Large outputs, audit trails
  logs/             # Debug events
```

**Why it matters:**
- Agents can resume by reading 2-5 small files, not scrolling giant chat history
- Failure recovery is built-in
- Audit trail exists by default
- Context window stays bounded

**EvoClaw adoption:**
- ✅ We already have this with tiered memory (hot/warm/cold + daily notes)
- 🔄 **Missing:** Structured run tracking with tasks.md checklist pattern
- 🔄 **Missing:** Automatic archival when tasks complete

### 2. **Approval Gates for Side Effects**

Ship-Faster treats certain actions as **high-risk**:
- Deployments (Vercel, Cloudflare)
- Database writes (UPDATE/DELETE without WHERE refused)
- Payments (Stripe operations)
- Destructive ops (force push, delete)

**Pattern:**
1. Write approval plan into tasks.md
2. Reference details in evidence/
3. Ask for confirmation
4. Only then execute

**EvoClaw adoption:**
- ✅ We have memory confirmation for storage
- 🔄 **Missing:** Systematic approval gates for:
  - ClawChain transactions (token transfers, staking)
  - Hyperliquid/Polymarket trades
  - Email sends, social posts
  - Server commands (restarts, updates)

### 3. **Progressive Disclosure (Skill Structure)**

Skills use this pattern:
```
<skill>/
  SKILL.md               # Entry point (when/why/inputs/outputs)
  foundation.md          # Step 1 details
  design.md              # Step 2 details
  deploy.md              # Step 3 details
  references/
    artifact-contract.md # Detailed specs
    troubleshooting.md   # Edge cases
  scripts/
    validate.py          # Automation
```

**Why:**
- Keep SKILL.md short (routing + constraints + output contract)
- Load step files only when executing that step
- References are opt-in (progressive disclosure)

**EvoClaw adoption:**
- ✅ We have SKILL.md structure
- 🔄 **Missing:** Consistent use of references/ for deep docs
- 🔄 **Missing:** scripts/ pattern for automation (most skills use shell inline)

### 4. **Skill Evolution (Self-Improvement)**

**Hooks system:**
- `PreToolUse` / `PostToolUse` hooks capture failures
- Writes to `runs/evolution/<run_id>/failures.json`
- `skill-improver` analyzes failures → generates patch suggestions
- Human reviews and applies patches

**Key constraint:** No auto-editing. Always suggest, never mutate.

**EvoClaw adoption:**
- ✅ We have agent-self-governance (WAL, VBR, ADL)
- 🔄 **Missing:** Systematic failure logging
- 🔄 **Missing:** Automated patch generation from failures
- 💡 **Opportunity:** This could feed into our self-evolution loop

### 5. **Composable Workflows**

Workflows are chains of skills with path-only I/O:
```python
# workflow-ship-faster calls:
tool-design-style-selector(repo_root, run_dir) → design-system.md
workflow-feature-shipper(repo_root, run_dir, feature_spec) → code changes
review-quality(repo_root, run_dir) → verdict
```

**Rules:**
- Pass **paths only**, not content (avoid context bloat)
- Each skill writes artifacts to canonical locations
- Workflows coordinate, skills execute

**EvoClaw adoption:**
- ✅ We use sub-agents for delegation
- 🔄 **Missing:** Standardized path-based I/O contracts
- 🔄 **Missing:** Artifact-first pattern (we rely on chat history)

## 🚀 What We Should Adopt for EvoClaw/ClawChain

### High Priority (Immediate Value)

#### 1. **Runs System for Agent Tasks**
Create `runs/` pattern for long-running agent work:

```
~/clawd/runs/
  clawchain-deploy-2026-02-16/
    proposal.md        # Deploy testnet validator
    tasks.md           # [ ] Build binary
                       # [x] Upload to VPS
                       # [ ] Start node
                       # [ ] Verify sync
    context.json       # {network: "testnet", vps: "135.181.157.121"}
    evidence/
      node-logs.txt
      sync-status.json
```

**Benefits:**
- Resume interrupted deploys
- Audit trail for blockchain ops
- Clear checkpoint system

**Implementation:**
- Add `run-manager.sh` skill
- Update AGENTS.md to use runs/ for multi-step tasks
- Integrate with tiered memory (runs summary → warm memory)

#### 2. **Approval Gates for High-Risk Actions**

Define risk tiers:

| Tier | Actions | Gate |
|------|---------|------|
| **Critical** | Token transfers, staking, payments | Write plan + wait for approval |
| **High** | Social posts, emails, server commands | Show plan, ask confirmation |
| **Medium** | File writes, git commits | Log intent, proceed |
| **Low** | File reads, queries | Proceed silently |

**Implementation:**
- Create `approval-gate.sh` wrapper
- Update SOUL.md with risk classification
- Add `APPROVALS.md` guide for common operations

#### 3. **Failure Logging + Evolution Loop**

Capture failures systematically:

```json
// runs/evolution/2026-02-16-session/failures.json
[
  {
    "timestamp": 1739664000,
    "tool": "exec",
    "command": "ssh peter@10.0.0.44 'systemctl start comfyui'",
    "error": "Permission denied (publickey)",
    "context": "Trying to start ComfyUI service",
    "skill": "gpu-media-pipeline"
  }
]
```

**Evolution workflow:**
1. Session end → analyze failures
2. Group by skill + error pattern
3. Generate patch suggestions
4. Store in `runs/evolution/patches/<skill>.md`
5. Human reviews, applies

**Benefits:**
- Fix recurring issues permanently
- Skills get smarter over time
- Audit what changed and why

### Medium Priority (Quality of Life)

#### 4. **Progressive Disclosure for Complex Skills**

Refactor heavy skills (ClawChain, Hyperliquid, Polymarket) to use:

```
skills/clawchain/
  SKILL.md              # When to use, basic examples
  references/
    rpc-api.md          # Full RPC reference
    pallets.md          # Pallet details
    troubleshooting.md  # Common errors
  scripts/
    query-balance.sh
    submit-extrinsic.sh
```

**Benefits:**
- Faster skill loading
- Less context window waste
- Easier to maintain

#### 5. **Structured Task Tracking (tasks.md)**

Adopt checklist pattern for multi-step work:

```markdown
# Tasks

## Status: active

## Next Action
- [ ] Deploy pallet-agent-registry to testnet
- [ ] Test DID registration flow

## Approvals
- [ ] **APPROVAL REQUIRED**: Deploy to testnet (overwrites existing)
      Details: evidence/deploy-plan.md
      Confirm: yes/no

## Completed
- [x] Build ClawChain binary
- [x] Upload to VPS
```

**Benefits:**
- Clear resume points
- Explicit approval tracking
- Visual progress

### Low Priority (Nice to Have)

#### 6. **Template System for Common Workflows**

Create templates/ for:
- `001-new-clawchain-pallet/` — Scaffold new pallet
- `002-deploy-testnet-node/` — Deploy validator
- `003-hackathon-submission/` — Package project for submission

**Benefits:**
- Faster iteration on common tasks
- Consistent structure
- Reproducible workflows

#### 7. **Auto-Archive Completed Runs**

Move completed runs to archive/:
```bash
runs/ship-faster/active/abc123/       # Working
→ runs/ship-faster/archive/2026-02-16-abc123/  # Done
```

**Benefits:**
- Clean workspace
- Searchable history
- Automatic organization

## 🧪 What NOT to Adopt

### ❌ Next.js-Specific Workflows
Ship-Faster is heavily Next.js/Vercel/Supabase focused. We don't need:
- Foundation checks (we're not building web apps)
- Design system workflows
- SEO tooling
- React/UI review skills

### ❌ MCP Integration Layer
Ship-Faster has MCP adapters for Stripe/Supabase/Cloudflare. We don't use MCP, we use native tools.

### ❌ Skills.sh Packaging
We use clawhub.com, not skills.sh ecosystem.

## 📋 Action Items for EvoClaw

### Phase 1: Foundation (1 day)
- [ ] Create `run-manager` skill with runs/ pattern
- [ ] Add approval-gate wrapper script
- [ ] Update AGENTS.md to use runs/ for multi-step work

### Phase 2: Evolution (2 days)
- [ ] Implement failure logging (runs/evolution/)
- [ ] Create skill-improver logic (failure → patch)
- [ ] Test on 3 existing skills

### Phase 3: Refactor (3 days)
- [ ] Refactor ClawChain skill to use references/
- [ ] Refactor Hyperliquid skill to use references/
- [ ] Add scripts/ to 5+ skills

### Phase 4: Templates (1 day)
- [ ] Create 3 common workflow templates
- [ ] Document template system

## 💡 Key Takeaways

**What Ship-Faster does brilliantly:**
1. **Context management** — Artifact-first prevents history bloat
2. **Safety** — Approval gates prevent costly mistakes
3. **Resumability** — Failures don't lose progress
4. **Evolution** — Skills improve from real usage

**What's different for EvoClaw:**
- We're blockchain/trading/infra focused, not web apps
- We already have strong memory (tiered system)
- We need approval gates for financial ops, not deployments

**Adoption strategy:**
- Take the **patterns** (runs, approval gates, failure logging)
- Skip the **domain specifics** (Next.js, Vercel, React)
- Adapt to **our domain** (blockchain, trading, edge agents)

**ROI estimate:**
- Runs system: **High** — solves resume problem immediately
- Approval gates: **High** — prevents costly trading/transfer mistakes
- Failure logging: **Medium** — long-term skill quality
- Progressive disclosure: **Medium** — cleaner skills, faster loading
- Templates: **Low** — nice to have, not urgent

## 🎯 Recommendation

**Start with Runs + Approval Gates** (Phase 1). These solve immediate pain points:
- Long blockchain deploys that fail mid-way → runs/ makes resume trivial
- Risky Hyperliquid trades → approval gates prevent fat-finger errors

Then **add evolution loop** (Phase 2) to systematically improve skills over time.

**Expected timeline:** 4-7 days to full adoption (parallel with ClawChain work)

---

**References:**
- Ship-Faster repo: https://github.com/bowen31337/ship-faster
- Runs concept: /tmp/ship-faster/docs/concepts/runs-and-approvals.md
- Skill system: /tmp/ship-faster/docs/concepts/skill-system.md
