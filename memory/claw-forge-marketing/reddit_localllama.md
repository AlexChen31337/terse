# Reddit Post — r/LocalLLaMA

**Title:** claw-forge: run autonomous coding agents fully locally with Ollama — no API key, no rate limits, YOLO mode included

---

**Body:**

If you've been wanting to run autonomous AI coding agents on your projects without handing data to a cloud API, **claw-forge** supports Ollama as a first-class provider. No API key. No rate limits. Your hardware, your models, your code stays local.

## How it works with Ollama

Point it at your local Ollama instance and pick your model:

```yaml
providers:
  - name: local-ollama
    type: ollama
    base_url: http://localhost:11434
    model: qwen2.5-coder:7b
    priority: 1
    rpm_limit: 999
```

Set priority: 1 and it runs Ollama first. The circuit breaker only kicks in if Ollama actually errors — high rpm_limit means it won't throttle itself on a local server. Works with any model Ollama supports: qwen2.5-coder, deepseek-coder, codellama, mistral, whatever you have pulled.

## What claw-forge does

Give it a spec file describing what you want built. It parses it into a feature dependency graph and runs parallel agents to implement features in order. Agents write code, tests, and do review. Live Kanban board shows what's happening (`claw-forge ui`).

```
claw-forge init
claw-forge plan      # spec → feature DAG
claw-forge run       # parallel agents go
```

## YOLO mode

`claw-forge run --yolo`

No verification gates. No review cycles between steps. Maximum throughput. If you're running locally and want to see what your models can do without guardrails, this is the flag. Useful for fast iteration when you understand the tradeoffs.

## Multi-provider fallback

You can stack Ollama + cloud providers. If Ollama falls over (OOM on a big context, etc.), it fails over to Groq or Anthropic automatically. Circuit breakers handle the routing. Run `claw-forge pool-status` to see which providers are healthy.

## The details

- Pure Python, zero Node.js in the core
- 18 pre-installed skills (6 LSP servers, debugging, verification, parallel dispatch)
- 1063 tests, ≥90% coverage, mypy clean
- Plugin system for adding your own models/providers
- Works on existing codebases (brownfield support)
- TDD bug fix: `claw-forge fix` — RED to GREEN protocol

`pip install --pre claw-forge`

Repo: https://github.com/clawinfra/claw-forge

Curious what models people are running locally for coding tasks — would love to hear what works well with this kind of agentic loop.
