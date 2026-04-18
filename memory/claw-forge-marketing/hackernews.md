# HackerNews Show HN Post

**Title:** Show HN: claw-forge – autonomous coding agents that run until all features pass

---

**Body:**

claw-forge is a Python tool that takes a spec (plain text or XML) and runs parallel AI coding agents on your project until every feature in the spec is implemented and passing. It parses the spec into a dependency DAG, assigns agents to features in topological order, and tracks progress on an optional live Kanban board. The idea is to get from "here's what I want built" to "all tests green" with minimal human intervention.

Technically: it's built on asyncio TaskGroup for parallel execution, uses the Claude Agent SDK, and ships with a multi-provider pool (Anthropic, AWS Bedrock, Azure Vertex, Groq, Ollama, and others) with auto-failover and per-provider RPM tracking. If a provider rate-limits you mid-run, it circuit-breaks and routes to the next available one. 18 skills are pre-installed — 6 LSP servers covering Python, Go, Rust, TypeScript, Solidity, and C++, plus systematic debugging, verification gate, and parallel dispatch. Agents use these skills automatically during planning and implementation. The plugin system is Python entry points, so you can add your own skills or providers without forking. Pure Python, zero Node.js (the optional Kanban UI is the only exception).

Current status: 1063 tests passing, ≥90% coverage, mypy clean. Pre-release on PyPI (pip install --pre claw-forge). Works on greenfield projects and existing brownfield codebases. There's a --yolo flag that disables verification gates for when you want raw speed. TDD bug fixing is a first-class workflow via claw-forge fix, which enforces RED to GREEN: write the failing test, then fix until it passes.

I'd welcome feedback on the provider pool design, the spec format (currently plain text with an XML dialect for structured feature definitions), and whether the skill system is the right abstraction for agent tooling. Repo: https://github.com/clawinfra/claw-forge
