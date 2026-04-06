# Caveman Skill

> 🪨 why use many token when few token do trick

Compressed output mode for Claude Code / Codex agents. Cuts ~65–75% of output tokens by stripping filler words, pleasantries, articles, and hedging — while keeping code, technical terms, and error messages verbatim.

Based on: https://github.com/JuliusBrussee/caveman

---

## When to Use

Use this skill when spawning sub-agents for:
- Code tasks (debug, refactor, explain)
- Short Q&A, lookup, summarize
- Any task where brevity > polish

**Don't use for:**
- Final user-facing content (blog posts, emails, MbD articles)
- Payhip book generation
- Any output Bowen will read directly without editing

---

## Compression Levels

### Lite (default)
- Drop filler phrases ("I'd be happy to", "Great question", "In conclusion")
- Drop redundant hedging ("it might be", "you could potentially")
- Keep full sentences, just cleaner

**System prefix:**
```
Be concise. Skip filler phrases, pleasantries, and unnecessary hedging. Keep technical terms and code verbatim.
```

### Full
- Drop articles (a, an, the) where meaning is clear
- Drop "I" subject where implicit
- Use fragment sentences for steps/lists
- Code blocks and error messages: always verbatim

**System prefix:**
```
CAVEMAN MODE: Omit articles, filler, pleasantries. Use fragments. Steps as bare imperatives. Keep code/errors verbatim. No apologies. No "I". Just signal.
```

### Ultra
- Maximum compression — every non-essential word dropped
- 1-3 word labels for concepts
- Numbered steps with no prose
- Reserved for: internal agent notes, tool-to-tool handoffs

**System prefix:**
```
ULTRA CAVEMAN: Max compress. Drop ALL non-essential words. Labels only. No sentences. Keep code verbatim.
```

---

## Benchmarks (from repo)

| Task | Normal tokens | Caveman tokens | Saved |
|------|--------------|----------------|-------|
| React re-render bug | 1180 | 159 | 87% |
| PostgreSQL pool setup | 2347 | 380 | 84% |
| Git rebase conflict | 891 | 374 | 58% |
| Average | — | — | **~65–75%** |

March 2026 paper finding: brevity constraints improved accuracy by 26pp (less hedging = more direct answers).

---

## How to Use

### In sessions_spawn
```python
sessions_spawn(
    task="[CAVEMAN FULL]\n\nExplain why this Go function leaks goroutines:\n\n```go\n...\n```",
    model="CC-Sonnet46"  # or any model
)
```

### Via helper script
```bash
uv run python ~/.openclaw/workspace/skills/caveman/scripts/caveman_prompt.py --level full "your task here"
```

### Manual prefix
Prepend to any sub-agent task prompt:
```
CAVEMAN MODE: Omit articles, filler, pleasantries. Use fragments. Steps as bare imperatives. Keep code/errors verbatim. No apologies. No "I". Just signal.

[your actual task here]
```

---

## Model Pairing

| Level | Best model | Why |
|-------|-----------|-----|
| Lite | Any | Minimal instruction overhead |
| Full | Sonnet 4.6 | Follows compression well, still accurate |
| Ultra | Haiku 4.5 | Cheap + short = ultra-efficient |

For coding tasks: Full + Sonnet 4.6 is the sweet spot.

---

## Integration with Other Skills

- **orchestrator**: Pass caveman prefix in Builder task prompts
- **clawmemory**: Captured facts are already terse; no change needed
- **knowledge-base**: Search results → caveman summary → save tokens in context

---

## Files
- `SKILL.md` — this file
- `scripts/caveman_prompt.py` — helper to generate prefixed prompts
