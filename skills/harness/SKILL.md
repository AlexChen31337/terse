# harness — Agent Engineering Harness

Implements the [OpenAI Codex team's agent-first engineering harness pattern](https://openai.com/index/harness-engineering/)
for any repo: short AGENTS.md TOC, structured docs/, custom linters with agent-readable errors,
CI enforcement, execution plan templates, doc-gardening.

## When to use
- Setting up a new repo for agent-first development
- Upgrading an existing repo's AGENTS.md to table-of-contents style
- Adding architectural lint enforcement to a repo
- Any repo where agents are doing most of the coding

## Usage

```bash
SKILL_DIR="$HOME/.openclaw/workspace/skills/harness"

# Scaffold harness for a repo (language auto-detected: Rust/Go/TypeScript)
uv run python "$SKILL_DIR/scripts/scaffold.py" --repo /path/to/repo

# Scaffold with force-overwrite of existing AGENTS.md
uv run python "$SKILL_DIR/scripts/scaffold.py" --repo /path/to/repo --force

# Run lints locally
bash /path/to/repo/scripts/agent-lint.sh

# Check doc freshness (finds stale references in docs/)
uv run python "$SKILL_DIR/scripts/doc_garden.py" --repo /path/to/repo --dry-run

# Check doc freshness and open a fix PR
uv run python "$SKILL_DIR/scripts/doc_garden.py" --repo /path/to/repo --pr

# Generate execution plan for a complex task
uv run python "$SKILL_DIR/scripts/plan.py" \
  --task "Add IBC timeout handling" \
  --repo /path/to/repo
```

## What gets created

| File | Description |
|------|-------------|
| `AGENTS.md` | ~100 line table of contents, pointers to docs/ |
| `docs/ARCHITECTURE.md` | Layer diagram + dependency rules (auto-generated from repo structure) |
| `docs/QUALITY.md` | Coverage targets + security invariants |
| `docs/CONVENTIONS.md` | Naming rules (language-specific) |
| `docs/EXECUTION_PLAN_TEMPLATE.md` | Structured plan format for complex tasks |
| `scripts/agent-lint.sh` | Custom linter with agent-readable errors (WHAT / FIX / REF) |
| `.github/workflows/agent-lint.yml` | CI gate on every PR |

## Lint error format

Every lint error produced by `scripts/agent-lint.sh` follows this format:
```
LINT ERROR [<rule-id>]: <description of the problem>
  WHAT: <why this is a problem>
  FIX:  <exact steps to resolve it>
  REF:  <which doc to consult>
```

This means agents can read lint output and fix problems without asking a human.

## Safety

- **Never overwrites existing AGENTS.md** without `--force` flag
- Reads existing code structure before generating docs (no hallucinated APIs)
- All writes are previewed in `--dry-run` mode before committing

## References

- [OpenAI Codex harness engineering](https://openai.com/index/harness-engineering/)
- [ClawChain harness PR](https://github.com/clawinfra/claw-chain/pull/64)
- [EvoClaw harness PR](https://github.com/clawinfra/evoclaw/pull/27)
