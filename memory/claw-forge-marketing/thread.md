# claw-forge Twitter/X Thread

---

1/9

claw-forge runs AI coding agents on your project until all features pass. Give it a spec. It spins up parallel agents, builds a dependency graph, implements everything in order, and tracks progress on a live Kanban board.

pip install --pre claw-forge

---

2/9

The workflow is four commands:

claw-forge init
/create-spec (describe what you want to build)
claw-forge plan
claw-forge run

That's it. Agents plan, implement, test, and review — without you babysitting them.

---

3/9

Nine provider pool: Anthropic, AWS Bedrock, Azure, Vertex, Groq, Ollama, and more. Auto-failover, circuit breakers, RPM tracking built in. If one provider rate-limits you, it switches automatically. You never hit a wall mid-run.

claw-forge pool-status to see live health.

---

4/9

18 pre-installed skills ship out of the box:

- 6 LSP servers: Python, Go, Rust, TypeScript, Solidity, C++
- Systematic debugging protocol
- Verification gate
- Parallel dispatch
- TDD bug fix (RED to GREEN)

Agents know how to use them automatically.

---

5/9

For bug fixes, it uses RED to GREEN protocol. Write the failing test first, then fix the code until it passes. No more "fixed it" PRs with no test coverage.

claw-forge fix — TDD discipline, automated.

---

6/9

Pure Python. Zero Node.js dependency (optional Kanban UI is the only exception). Python 3.12+, asyncio TaskGroup, mypy clean. 1063 tests passing, 90%+ coverage. Not a prototype.

Greenfield and brownfield both supported — works on existing codebases too.

---

7/9

YOLO mode exists for when you want max speed and no guardrails:

claw-forge run --yolo

No verification gates. No review cycles. Just agents going full send. Use it when you understand the risks and need to ship fast.

---

8/9

Plugin system via Python entry points. Add your own skills, providers, or agent behaviours. The provider pool config is YAML — swap models, add endpoints, tune RPM limits without touching code.

Built to be extended, not just used.

---

9/9

claw-forge is open source under ClawInfra. Built by @unoclaw.

Repo: https://github.com/clawinfra/claw-forge
PyPI: https://pypi.org/project/claw-forge/

Star it if you want autonomous coding agents that actually finish the job.
