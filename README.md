# terse

> 🪨 why use many token when few token do trick

Compressed output mode for AI agents. Cuts ~65–75% of output tokens by stripping filler words, pleasantries, articles, and hedging — while keeping code, technical terms, and error messages verbatim.

Based on [caveman](https://github.com/JuliusBrussee/caveman).

## Token Savings

| Task | Normal | Terse | Saved |
|------|--------|-------|-------|
| React re-render bug | 1180 | 159 | 87% |
| PostgreSQL pool setup | 2347 | 380 | 84% |
| Git rebase conflict | 891 | 374 | 58% |

March 2026 paper: brevity constraints improved accuracy by 26pp.

## Levels

- **lite** — Drop filler, hedging. Full sentences.
- **full** — Omit articles, use fragments, bare imperatives.
- **ultra** — Max compress. Labels only. No sentences.

## Quick Start

```bash
# Install as OpenClaw skill
clawhub install terse

# Or manual: copy to ~/.openclaw/workspace/skills/terse/
```

### CLI helper

```bash
uv run python scripts/caveman_prompt.py --level full "your task here"
```

### In sub-agent prompts

```
CAVEMAN MODE: Omit articles, filler, pleasantries. Use fragments.
Steps as bare imperatives. Keep code/errors verbatim. No apologies.
No "I". Just signal.

[your task]
```

## Model Pairing

| Level | Best model | Why |
|-------|-----------|-----|
| Lite | Any | Minimal overhead |
| Full | Sonnet 4.6 | Follows compression well |
| Ultra | Haiku 4.5 | Cheap + short = efficient |

## License

MIT
