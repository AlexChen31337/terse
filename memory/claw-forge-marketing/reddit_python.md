# Reddit Post — r/Python

**Title:** claw-forge: a pure Python autonomous coding agent harness — give it a spec, it runs agents until all features pass (asyncio, mypy clean, 90%+ coverage)

---

**Body:**

Hey r/Python — I wanted to share something I've been working on: **claw-forge**, an open-source tool that runs parallel AI coding agents on your project until every feature in a spec is implemented and tested.

## What it does

You write a spec (plain text or a structured XML format), run `claw-forge plan` to parse it into a dependency DAG, then `claw-forge run` to kick off parallel agents. Agents implement features in dependency order, write tests, fix bugs, and do code review. Progress is tracked on an optional live Kanban board (`claw-forge ui`).

## Why pure Python matters

No Node.js in the core pipeline. Everything is Python 3.12+ with asyncio TaskGroup for concurrency. The optional Kanban UI is the only piece that touches Node. If you're already in a Python environment, `pip install --pre claw-forge` and you're done. Works great with `uv`.

## The provider pool

The multi-provider pool is probably the most interesting piece technically. Config is YAML:

```yaml
providers:
  - name: anthropic
    type: anthropic
    rpm_limit: 60
    priority: 1
  - name: groq
    type: groq
    rpm_limit: 30
    priority: 2
  - name: ollama
    type: ollama
    base_url: http://localhost:11434
    model: qwen2.5-coder:7b
    priority: 3
```

Each provider has a circuit breaker. If one rate-limits or errors, claw-forge fails over to the next in priority order automatically. RPM tracking is per-provider in memory. You can add as many as you want — Anthropic, Bedrock, Azure, Vertex, Groq, Ollama all work out of the box.

## Quality bar

- 1063 tests passing
- ≥90% coverage enforced in CI
- mypy clean throughout
- Plugin system via Python entry points (add your own skills or providers)
- 18 pre-installed skills: 6 LSP servers (Python/Go/Rust/TS/Solidity/C++), systematic debugging, verification gate, parallel dispatch

## Current status

Pre-release on PyPI. Greenfield and brownfield projects both work. The TDD bug fix workflow (`claw-forge fix`) enforces RED to GREEN — write the failing test first, then the agents fix it.

`pip install --pre claw-forge`

Repo: https://github.com/clawinfra/claw-forge

Happy to answer questions about the asyncio design, the provider pool, or the skill system. Feedback welcome.
