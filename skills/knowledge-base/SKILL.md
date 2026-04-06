---
name: knowledge-base
description: Karpathy-style LLM Knowledge Base — Ingest raw files, compile into structured wiki with backlinks, lint for consistency. No RAG, no vector DB. Just markdown + LLM librarian.
homepage: https://github.com/AlexChen31337/llm-knowledge-base
metadata: {"clawdbot":{"emoji":"📚","requires":{"bins":["uv"]}}}
---

# Knowledge Base Skill

Karpathy's "LLM Knowledge Base" methodology as an OpenClaw skill. The LLM acts as an active librarian — ingesting raw materials, compiling structured wiki articles with backlinks, and linting for consistency.

**Three-stage loop:** Ingest → Compile → Lint

## Core Philosophy

- **File-over-app:** Markdown files are source of truth. No vendor lock-in.
- **LLM as librarian:** Not passive search — active synthesis, writing, and self-healing.
- **No RAG needed:** At human scale (~100 articles, ~400K words), structured indices + summaries are sufficient.
- **Obsidian-compatible:** `[[backlinks]]` for knowledge graph navigation.

## Commands

All scripts run from the knowledge-base repo. Use `uv run python` for all execution.

### Ingest Raw Materials

```bash
cd /tmp/llm-knowledge-base
uv run python scripts/ingest.py url "https://arxiv.org/abs/1706.03762"
uv run python scripts/ingest.py file "my_paper.pdf"
uv run python scripts/ingest.py dir "./my_docs/"
```

### Compile Wiki

```bash
uv run python scripts/compile.py
```

This reads all files in `raw/`, synthesizes structured articles into `wiki/` with:
- Encyclopedia-style articles per concept
- `[[backlinks]]` between related ideas
- Summary files for each source
- `INDEX.md` navigation hub

### Lint / Health Check

```bash
uv run python scripts/lint.py
```

Scans wiki for:
- Broken `[[backlinks]]`
- Missing sections or gaps
- Inconsistencies between articles
- New connections to add
- Outdated information

Auto-fixes what it can, flags what needs human review.

### Search

```bash
uv run python scripts/search.py "transformer attention mechanism"
```

Full-text search over wiki. No vector DB — just grep/FTS.

### Serve Locally

```bash
uv run python scripts/serve.py
# Opens http://localhost:8000
```

## Domain Forking

To create a domain-specific knowledge base:

1. Copy this skill directory: `cp -r skills/knowledge-base skills/knowledge-base-<domain>`
2. Edit `config.yaml` — set domain-specific templates and schema
3. Edit `templates/` — customize compilation and linting prompts for the domain
4. Run the ingest→compile→lint loop with domain-specific raw materials

**Example domains:**
- `knowledge-base-crypto` — whitepapers, tokenomics, audit reports
- `knowledge-base-codebase` — source code → architecture docs, API reference
- `knowledge-base-research` — papers, courses → study wiki with spaced repetition
- `knowledge-base-competitive` — competitor tracking, market intelligence

## Agent Integration

When running as part of an agent workflow:

1. **During normal work:** Agent drops URLs/files into `raw/` via `ingest.py`
2. **On schedule (cron):** Run `compile.py` to synthesize new raw materials
3. **Nightly:** Run `lint.py` for health checks and self-healing
4. **On demand:** Agent queries wiki via `search.py` instead of re-researching

## Multi-Agent Pattern

For compound loops with multiple agents:

1. Sub-agents write findings to `raw/` 
2. Compiler agent runs `compile.py` to synthesize
3. Quality gate agent validates with `lint.py` before promotion
4. Verified wiki articles fed back as context for next agent session

See `docs/multi-agent.md` in the repo for full pattern.

## Config

```yaml
# config.yaml
llm:
  provider: openai  # openai | anthropic | ollama
  model: gpt-4o
  max_tokens: 4096

paths:
  raw_dir: "./raw"
  wiki_dir: "./wiki"
  templates_dir: "./templates"

wiki:
  create_backlinks: true
  create_summaries: true
  create_index: true
```

## Key Insight

> *"At ~100 articles / ~400K words, LLM navigation via summaries and index files is more than sufficient. No vector DB needed."*

The bottleneck is synthesis quality, not retrieval speed. Pre-compiled wiki articles are richer and more useful than on-the-fly RAG chunks.
