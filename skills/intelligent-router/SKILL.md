---
name: intelligent-router
description: Intelligent model routing for sub-agent task delegation. Choose the optimal model based on task complexity, cost, and capability requirements. Reduces costs by routing simple tasks to cheaper models while preserving quality for complex work.
version: 3.0.0
core: true
---

# Intelligent Router — Core Skill

> **CORE SKILL**: This skill is infrastructure, not guidance. Installation = enforcement.
> Run `bash skills/intelligent-router/install.sh` to activate.

## What It Does

Automatically classifies any task into a tier (SIMPLE/MEDIUM/COMPLEX/REASONING/CRITICAL)
and recommends the cheapest model that can handle it well.

**The problem it solves:** Without routing, every cron job and sub-agent defaults to Sonnet
(expensive). With routing, monitoring tasks use free local models, saving 80-95% on cost.

---

## MANDATORY Protocol (enforced via AGENTS.md)

### Before spawning any sub-agent:
```bash
python3 skills/intelligent-router/scripts/router.py classify "task description"
```

### Before creating any cron job:
```bash
python3 skills/intelligent-router/scripts/spawn_helper.py "task description"
# Outputs the exact model ID and payload snippet to use
```

### To validate a cron payload has model set:
```bash
python3 skills/intelligent-router/scripts/spawn_helper.py --validate '{"kind":"agentTurn","message":"..."}'
```

### ❌ VIOLATION (never do this):
```python
# Cron job without model = Sonnet default = expensive waste
{"kind": "agentTurn", "message": "check server..."}  # ← WRONG
```

### ✅ CORRECT:
```python
# Always specify model from router recommendation
{"kind": "agentTurn", "message": "check server...", "model": "ollama/glm-4.7-flash"}
```

---

## Tier System

| Tier | Use For | Primary Model | Cost |
|------|---------|---------------|------|
| 🟢 SIMPLE | Monitoring, checks, summaries | `ollama/glm-4.7-flash` | FREE |
| 🟡 MEDIUM | Code fixes, patches, research | DeepSeek V3.2 | $0.40/M |
| 🟠 COMPLEX | Features, architecture, debug | Sonnet 4.5 | $3/M |
| 🔵 REASONING | Proofs, formal logic | DeepSeek R1 32B | $0.20/M |
| 🔴 CRITICAL | Security, production | Opus 4.6 | $5/M |

**SIMPLE fallback chain:** `ollama/glm-4.7-flash` → `anthropic-proxy-4/glm-4.7` → `anthropic-proxy-6/glm-4.5-air`

---

## Installation (Core Skill Setup)

Run once to self-integrate into AGENTS.md:
```bash
bash skills/intelligent-router/install.sh
```

This patches AGENTS.md with the mandatory protocol so it's always in context.

---

## CLI Reference

```bash
# Classify + recommend model
python3 skills/intelligent-router/scripts/router.py classify "task"

# Get model id only (for scripting)
python3 skills/intelligent-router/scripts/spawn_helper.py --model-only "task"

# Show spawn command
python3 skills/intelligent-router/scripts/spawn_helper.py "task"

# Validate cron payload has model set
python3 skills/intelligent-router/scripts/spawn_helper.py --validate '{"kind":"agentTurn","message":"..."}'

# List all models by tier
python3 skills/intelligent-router/scripts/router.py models

# Detailed scoring breakdown
python3 skills/intelligent-router/scripts/router.py score "task"

# Config health check
python3 skills/intelligent-router/scripts/router.py health
```

---

## Scoring System

15-dimension weighted scoring (not just keywords):

1. **Reasoning markers** (0.18) — prove, theorem, derive
2. **Code presence** (0.15) — code blocks, file extensions
3. **Multi-step patterns** (0.12) — first...then, numbered lists
4. **Agentic task** (0.10) — run, fix, deploy, build
5. **Technical terms** (0.10) — architecture, security, protocol
6. **Token count** (0.08) — complexity from length
7. **Creative markers** (0.05) — story, compose, brainstorm
8. **Question complexity** (0.05) — multiple who/what/how
9. **Constraint count** (0.04) — must, require, exactly
10. **Imperative verbs** (0.03) — analyze, evaluate, audit
11. **Output format** (0.03) — json, table, markdown
12. **Simple indicators** (0.02) — check, get, show (inverted)
13. **Domain specificity** (0.02) — acronyms, dotted notation
14. **Reference complexity** (0.02) — "mentioned above"
15. **Negation complexity** (0.01) — not, never, except

Confidence: `1 / (1 + exp(-8 × (score - 0.5)))`

---

## Config

Models defined in `config.json`. Add new models there, router picks them up automatically.
Local Ollama models have zero cost — always prefer them for SIMPLE tasks.
