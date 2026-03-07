# Harness Build Log

**Date:** 2026-03-08 00:15 AEDT
**Task:** Build agent engineering harness for clawinfra/claw-chain and clawinfra/evoclaw,
then package as a reusable OpenClaw skill.

---

## PRs Opened

| Repo | PR URL | Branch |
|------|--------|--------|
| clawinfra/claw-chain | https://github.com/clawinfra/claw-chain/pull/64 | feat/agent-harness |
| clawinfra/evoclaw | https://github.com/clawinfra/evoclaw/pull/27 | feat/agent-harness |

---

## Phase 1: ClawChain Harness (Rust/Substrate)

**Repo:** `/tmp/harness-clawchain` → `clawinfra/claw-chain`
**Commit:** `a325a36`

### Files created/modified:
- `AGENTS.md` — 102 lines, table of contents style, pointers to docs/
- `docs/ARCHITECTURE.md` — Updated with full 12-pallet dependency graph, Config trait boundary,
  bounded storage rules, weight annotation rules, event emission rules, runtime ordering
- `docs/QUALITY.md` — 90% coverage target, storage migration test rules, security-sensitive
  function rules (update_reputation, treasury_spend, invoke_service), benchmark requirements
- `docs/CONVENTIONS.md` — Naming rules: pallets (pallet-{domain}), extrinsics (verb_noun),
  events (PascalCase past tense), storage (PascalCase plural), weights (matching extrinsic name)
- `docs/EXECUTION_PLAN_TEMPLATE.md` — Structured plan template for complex tasks
- `scripts/agent-lint.sh` — 5 rules with WHAT/FIX/REF agent-readable error format:
  1. missing-benchmarks: all pallets must have benchmarking.rs
  2. unbounded-storage: Vec<T> in storage forbidden (use BoundedVec)
  3. missing-events: pallets with extrinsics must emit events
  4. missing-origin-check: security-sensitive extrinsics must validate origin
  5. agents-too-long: AGENTS.md must stay under 150 lines
- `.github/workflows/agent-lint.yml` — CI gate (agent-lint + clippy + tests on every PR)

### Pallets covered (12):
agent-did, agent-receipts, agent-registry, anon-messaging, claw-token,
gas-quota, ibc-lite, quadratic-governance, reputation, rpc-registry,
service-market, task-market

---

## Phase 2: EvoClaw Harness (Go)

**Repo:** `/tmp/harness-evoclaw` → `clawinfra/evoclaw`
**Commit:** `3dc3381`

### Files created:
- `AGENTS.md` — 127 lines, table of contents style, full package map
- `docs/ARCHITECTURE.md` — Layer diagram (cmd→internal→pkg), all 25+ internal package
  responsibilities, SKILLRL pipeline (observer→distiller→retriever→injector→updater),
  dependency injection pattern, testing architecture
- `docs/QUALITY.md` — 90% coverage target, testify/mock patterns, table-driven tests,
  goroutine lifecycle rules, error handling patterns
- `docs/CONVENTIONS.md` — Package naming, godoc requirements, interface design (1-3 methods),
  error types, context propagation rules, Python script conventions
- `docs/EXECUTION_PLAN_TEMPLATE.md` — Go-specific execution plan template
- `scripts/agent-lint.sh` — 5 rules:
  1. reverse-dependency: internal→cmd and pkg→internal forbidden
  2. missing-godoc: all exported symbols require godoc (via go vet)
  3. global-state: warning on exported package-level vars
  4. build-failure: go build ./... must pass
  5. agents-too-long: AGENTS.md under 150 lines
- `.github/workflows/agent-lint.yml` — CI with race detector (orchestrator, skillbank, agents)

### Key packages documented (25+):
orchestrator, skillbank, agents, evolution, genome, rsi, interfaces, config,
memory, models, router, clawchain, onchain, channels, cloud, scheduler, security,
wal, governance, saas, platform, updater, clawhub, types, migrate

---

## Phase 3: OpenClaw Skill

**Path:** `~/.openclaw/workspace/skills/harness/`

### Files created:
- `SKILL.md` — Usage guide with all CLI commands
- `scripts/scaffold.py` — Language-auto-detecting harness scaffolder:
  - Detects Rust/Go/TypeScript from Cargo.toml/go.mod/package.json
  - Reads real package structure (pallets/, internal/, src/)
  - Generates language-appropriate docs/ content
  - Never overwrites AGENTS.md without --force
  - --dry-run mode for safe preview
  - Generates CI yml adapted to language
- `scripts/doc_garden.py` — Stale reference detector:
  - Scans all docs/*.md for file/function/path references
  - Checks if referenced files/functions exist in codebase
  - --dry-run to preview
  - --pr to open a GitHub fix PR automatically
  - Found 28 stale refs in claw-chain docs on first run
- `scripts/plan.py` — Execution plan generator:
  - Heuristic package detection from task description
  - Complexity estimation (Low/Medium/High)
  - Language-appropriate step checklists
  - Writes to docs/plans/<slug>.md

### Skill tests (manual):
```bash
uv run python skills/harness/scripts/scaffold.py --repo /tmp/harness-clawchain --dry-run
# → Detected language: rust, 12 packages found

uv run python skills/harness/scripts/scaffold.py --repo /tmp/harness-evoclaw --dry-run
# → Detected language: go, 30 packages found

uv run python skills/harness/scripts/doc_garden.py --repo /tmp/harness-clawchain --dry-run
# → Found 28 stale references (real!)

uv run python skills/harness/scripts/plan.py \
  --task "Add IBC timeout handling to ibc-lite pallet" \
  --repo /tmp/harness-clawchain --dry-run
# → Generated High-complexity plan targeting ibc-lite pallet
```

---

## Design Decisions

1. **WHAT/FIX/REF error format** — Every lint error tells the agent what's wrong, how to fix it,
   and which doc to read. Agents can self-remediate without human review loops.

2. **Scaffold never overwrites AGENTS.md** — Protects existing work. --force required explicitly.

3. **Doc garden uses grep-based checks** — Fast, no AST parsing required. Some false positives
   on code examples in docs (e.g. `src/lib.rs` in a template). Acceptable trade-off.

4. **CI has separate jobs** — agent-lint, clippy/vet, tests, race-detector as separate jobs
   so failures are pinpointed without reading full CI log.

5. **AGENTS.md length enforced in CI** — Prevents doc sprawl that burns agent context budget.

---

## Files Structure

```
skills/harness/
  SKILL.md                   — usage guide
  scripts/
    scaffold.py              — scaffold harness for any repo
    doc_garden.py            — find stale doc references, open fix PRs
    plan.py                  — generate execution plans for complex tasks
```
