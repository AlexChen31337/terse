# How We Cut AI Agent Token Usage by 87% (and Beat Hermes at Its Own Game)

**Author:** Alex Chen  
**Date:** April 18, 2026  

---

Here's a number that should make every agent developer wince: **3,789 tokens.**

That's how many tokens OpenClaw was burning on every single conversation just to list its available skills. Not executing them. Not reading their docs. Just *listing* them in the system prompt so the agent knew they existed.

We had 150+ skills. Each one got a name, a description, and a file path injected into every session. Most of them were never used. It was like printing the entire menu of a 150-item restaurant and handing it to every customer who walked in asking for a coffee.

We fixed it. The result: **87.5% token reduction.** That beats the Hermes agent approach at its upper range.

Here's how.

## The Problem: Skills Are Expensive

OpenClaw is an open-source AI agent framework. Its power comes from a plugin system called "skills" — modular capability packages that teach the agent how to do everything from deploying Docker containers to trading on Polymarket.

Each skill has a `SKILL.md` file that describes what it does and how to use it. The standard approach is to inject all skill metadata into the system prompt so the agent knows what's available. With 150+ skills, that adds up fast:

- **15,158 characters** of skill metadata per session
- **~3,789 tokens** per conversation (estimated at 4 chars/token)
- Most of it completely irrelevant to the current task

Every token costs money. Every token adds latency. Every token is context window real estate that could be used for actual work.

## What Hermes Gets Right

The Hermes agent approach popularized lazy loading for agent tools. Instead of injecting full tool descriptions upfront, Hermes withholds content and loads it on demand. The claimed results: **70-90% token reduction**.

The core insight is sound: don't tell the agent about tools it won't use this session. A coding agent doesn't need weather API docs. A trading bot doesn't need blog publishing instructions.

But Hermes focuses on *withholding content*. The skill list itself — the catalog of what's available — still takes up space. It's like removing the chapters from a book but keeping the full table of contents.

## Our Approach: Four Layers of Optimization

We went deeper. Instead of just hiding content, we rethought the entire skill discovery pipeline.

### Layer 1: Conditional Metadata Filtering (11.3% reduction)

Not every skill makes sense on every machine. Our Go LSP skill is useless without `gopls` installed. Our Discord integration is pointless if Discord isn't configured. Our Whisper skill can't work without an OpenAI API key.

We added conditional metadata to each skill's `SKILL.md`:

```yaml
metadata.openclaw:
  requires:
    anyBins: ["gopls"]
  reason: "Go LSP — only useful with gopls installed"
```

At startup, the runtime checks which binaries are in `PATH`, which environment variables are set, and which channels are configured. Skills that don't match the current environment get filtered out.

On a typical development machine, this removed **22 of 194 skills** — an 11.3% reduction. Modest, but free. These skills were never going to work anyway.

### Layer 2: Skill Consolidation (87.5% reduction)

This was the big win. Instead of listing 80 individual skills, we grouped them into **15 categories** with a compact reference table:

| Category | Count | Example Skills |
|----------|-------|---------------|
| trading-prediction | 8 | polymarket, simmer, alphastrike |
| huggingface | 8 | huggingface-papers, hf-cli, llmfit |
| coding-agents | 3 | claude-code, harness, parallel-dispatch |
| content-media | 9 | mbd, payhip-publisher, youtube-content |

The full table takes **~475 tokens** instead of **3,789 tokens**. Same information density. The agent still knows every skill exists and what category it belongs to. It just doesn't get the full description upfront.

### Layer 3: On-Demand Search

We built a lightweight TF-IDF search script (`skill_search.py`) that ranks skills by relevance to the current task:

```bash
python3 skill_search.py "deploy docker container"
# Returns: docker-deploy (0.89), bird (0.42), claw-forge-cli (0.31)...
```

No external dependencies. No embedding model. Just keyword matching that runs in milliseconds. The agent calls this when it needs to find a skill, gets a ranked list, then loads only the top match.

### Layer 4: Lazy Content Loading

This is the Hermes-style optimization, and we were already doing it. The agent only reads a skill's full `SKILL.md` when it actually needs to execute that skill. No upfront loading. No wasted context.

But here's the difference: because Layer 2 already compressed the *discovery* phase, the agent has more context window available for the *execution* phase. It's a double win.

## The Results

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Skill listing characters | 15,158 | ~1,900 | 87.5% |
| Skill listing tokens | ~3,789 | ~475 | 87.5% |
| Skills filtered (env check) | 0 | 22 | 11.3% |
| Discovery search | None | TF-IDF | Instant |

**Combined: ~87.5% token reduction on the skill catalog alone.**

Compared to Hermes' 70-90% range, we're at the top of that bracket. And we achieve it through a fundamentally different mechanism — compressing the *index*, not just hiding the *content*.

## The Key Insight

Everyone focuses on lazy *loading*. We focused on lazy *listing*.

The breakthrough wasn't withholding skill documentation until it's needed — that's table stakes. The breakthrough was realizing that **the agent doesn't need to read 80 skill descriptions to know what's available.** A grouped table of 15 categories is enough context for the agent to search intelligently and load precisely.

Think of it this way: you don't need to read every app description in the App Store to find a calculator. You search "calculator" and get results. Our skill system works the same way. The compact category table is the App Store homepage. The TF-IDF search is the search bar. The full SKILL.md is the app detail page.

This pattern — compress the index, search on demand, load lazily — applies beyond skills. Any agent framework that injects large tool catalogs, knowledge bases, or capability lists into prompts can benefit from the same approach.

## Open Source

All of this is open source. The skill consolidation system, the TF-IDF search, the conditional metadata — it's all in the OpenClaw repository.

- **GitHub:** [github.com/openclaw/openclaw](https://github.com/openclaw/openclaw)
- **Docs:** [docs.openclaw.ai](https://docs.openclaw.ai)

The scripts are simple Python with zero dependencies. Drop them into any agent framework that struggles with token bloat from tool catalogs.

---

*We're building OpenClaw to be the most efficient open-source agent framework out there. Token efficiency isn't just about saving money — it's about giving agents more room to think. If you're interested in agent infrastructure, come contribute.*

— Alex Chen
