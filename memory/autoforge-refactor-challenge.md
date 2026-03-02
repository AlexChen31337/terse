# AutoForge Refactoring Challenge
*Alex Chen — 2026-03-02*

---

## What AutoForge Actually Is (Honest Assessment)

AutoForge is a well-engineered but architecturally conservative autonomous coding system. It keeps Claude Agent SDK at the core, wraps state in SQLite via MCP, and spawns agents as subprocesses coordinated by an asyncio loop. The ideas are sound. The execution has 6 structural problems I'd challenge you to fix.

---

## The 6 Challenges

---

### Challenge 1: Kill the Node.js wrapper. Pure Python, published to PyPI.

**Current:** `npm install -g autoforge-ai` → Node.js CLI bootstraps a Python venv → calls Python. Two runtimes, two package managers, Node.js required on every machine.

**Refactored:**
```toml
# pyproject.toml
[project]
name = "autoforge2"
requires-python = ">=3.11"
dependencies = ["claude-agent-sdk", "fastapi", "sqlalchemy", "typer", "rich"]

[project.scripts]
autoforge = "autoforge2.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

```bash
# Install and run — zero Node.js
uv tool install autoforge2
autoforge init my-project
autoforge run my-project --concurrency 4
autoforge serve my-project --port 8888
```

**Why this wins:**
- `uv tool install` handles venv isolation, no global pip pollution
- `uv` is already on the machine (you use it for everything else)
- Publish to PyPI: `uv build && uv publish`
- Single `pyproject.toml` instead of `package.json` + `requirements.txt` + `requirements-prod.txt`
- Removes the `lib/cli.js` bootstrap that does nothing but invoke Python anyway

---

### Challenge 2: MCP is the wrong tool for state management.

**Current:** AutoForge runs an MCP server (`feature_mcp.py`) per agent session. Each agent subprocess spawns its own MCP process. The MCP server is used as a database proxy — agents call `feature_claim_and_get`, `feature_mark_passing`, etc. over the MCP protocol.

**The problem:** MCP is a tool protocol designed to give LLMs access to external capabilities. Using it as a persistent state store couples your state to the LLM tool-call loop. When the SDK changes (and it will), your state layer breaks.

**Refactored: AgentStateService — a proper REST service agents call directly.**

```
autoforge/
├── state/
│   ├── service.py          # FastAPI app: /features, /sessions, /events
│   ├── models.py           # SQLAlchemy models (unchanged)
│   └── scheduler.py        # Dependency-aware scheduling (extracted from orchestrator)
├── skills/                 # Claude Code agent skills
│   ├── coding-agent/
│   │   └── SKILL.md        # Injected into every coding agent
│   ├── testing-agent/
│   │   └── SKILL.md
│   └── initializer/
│       └── SKILL.md
└── cli.py                  # Typer CLI
```

```python
# Agents call HTTP endpoints, not MCP tools
# GET  /features/next?session_id=xxx  → claim + return next feature
# POST /features/{id}/complete        → mark passing
# POST /features/{id}/fail            → mark failing + release
# GET  /events                        → SSE stream of real-time events
# WS   /ws                            → WebSocket for UI
```

**Why this wins:**
- State service runs as a single process — not spawned per agent
- Agents on different machines can participate (multi-machine parallelism)
- HTTP calls are observable, cacheable, and debuggable with standard tools
- Separates concerns cleanly: MCP stays for *capabilities*, REST stays for *state*
- The React UI talks to the same REST API — no special WebSocket-from-subprocess pipe

---

### Challenge 3: Replace subprocess+threading+asyncio with asyncio throughout.

**Current:** 3 concurrency models running simultaneously:
```
asyncio event loop (orchestrator)
  → subprocess.Popen (agent processes)
    → threading.Thread (output reader per process)
      → call_soon_threadsafe() to signal back
```

This is why `parallel_orchestrator.py` is 1,000+ lines. The `_signal_agent_completed()` dance exists entirely because threads can't touch asyncio objects directly.

**Refactored:** Every agent is an asyncio Task calling the Claude Agent SDK directly — no subprocesses, no threads.

```python
async def run_agent(feature_id: int, session_token: str, skill: AgentSkill) -> AgentResult:
    """One asyncio task per feature. No subprocess, no threads."""
    client = create_client(agent_type=skill.agent_type)
    prompt = await skill.build_prompt(feature_id, session_token)
    async with client:
        async for msg in client.query(prompt):
            yield msg

async def orchestrate(project_dir: Path, concurrency: int = 3):
    """Pure asyncio. No threads. No subprocesses."""
    async with asyncio.TaskGroup() as tg:
        for feature in await get_ready_features():
            tg.create_task(run_agent(feature.id, session_token, coding_skill))
```

**Why this wins:**
- `asyncio.TaskGroup` handles cancellation, error propagation, and cleanup automatically
- Eliminates `threading.Lock`, `threading.Event`, `call_soon_threadsafe`, `kill_process_tree`
- The orchestrator drops from ~1,000 lines to ~200
- Debugging a single asyncio task is trivially easier than a subprocess with a thread reader
- Claude Agent SDK already supports async — no wrapper needed

**Caveat to discuss:** If Claude Agent SDK spawns subprocesses internally (which it does — it calls the `claude` CLI), you still have child processes. But *you* don't manage them — the SDK does. That's the right abstraction boundary.

---

### Challenge 4: Agent skills as first-class plugins, not embedded `.claude/` files.

**Current:** `.claude/skills/`, `.claude/agents/`, `.claude/commands/` are bundled inside the AutoForge repo. Skills are static markdown files. Adding a new agent type means editing AutoForge's source.

**Refactored: Plugin protocol with entry points.**

```python
# Plugin protocol
class AgentPlugin(Protocol):
    name: str
    agent_type: Literal["initializer", "coding", "testing", "custom"]
    skill_path: Path        # SKILL.md location
    allowed_tools: list[str]
    max_turns: int
    
    async def build_prompt(self, context: AgentContext) -> str: ...
    async def on_complete(self, result: AgentResult) -> None: ...

# Register via pyproject.toml entry points
[project.entry-points."autoforge.plugins"]
coding = "autoforge2.plugins.coding:CodingAgentPlugin"
testing = "autoforge2.plugins.testing:TestingAgentPlugin"
# Third parties publish their own:
# my-security-auditor = "mysec.plugin:SecurityAuditPlugin"
```

```bash
# Install third-party agent plugins
uv pip install autoforge-plugin-security-auditor
autoforge plugins list
# → coding (built-in), testing (built-in), security-auditor (installed)

autoforge run my-project --plugins coding,security-auditor
```

**Why this wins:**
- Community can extend AutoForge without forking it
- Each plugin brings its own SKILL.md, which gets injected when that agent type runs
- Skills become composable: a coding agent can load `playwright-cli` skill on top of `coding-agent` base skill
- Versioned separately — security auditor plugin can update without AutoForge core changing
- Maps directly to OpenClaw's skill architecture (which you already know)

---

### Challenge 5: Session state continuity — agents shouldn't start cold.

**Current:** Every new Claude session starts with zero context. The agent must call MCP tools to discover its feature, read files to understand the codebase, etc. This is the main reason first sessions take 10-20 minutes — the agent is orienting itself from scratch.

**Refactored: Session manifest injected at startup.**

The AgentStateService writes a `session_manifest.json` before spawning each agent:

```json
{
  "session_id": "abc-123",
  "feature_id": 42,
  "feature_name": "User authentication flow",
  "feature_status": "in_progress",
  "prior_attempts": 1,
  "prior_errors": ["TypeError in auth.py:127 — missing await"],
  "files_modified": ["src/auth.py", "src/middleware.py", "tests/test_auth.py"],
  "last_test_result": {"passed": 3, "failed": 1, "error": "assertion failed line 47"},
  "dependencies_passing": [1, 3, 7],
  "git_branch": "feature/auth-flow",
  "last_commit": "fix: add await to session.get()"
}
```

The coding agent SKILL.md includes:
```markdown
## Session Start Protocol
1. Read `.autoforge/session_manifest.json`
2. If prior_attempts > 0: read prior_errors and files_modified FIRST
3. Run `git log --oneline -5` to see recent commits
4. Call /features/{id} to get full feature spec
5. ONLY THEN start implementation
```

**Why this wins:**
- Agents start oriented — no 5-minute "what am I doing?" phase
- Prior errors are explicitly surfaced — no repeating the same mistake
- Modified files list is pre-loaded — agent doesn't waste turns discovering the codebase
- This is exactly what your WAL + active_task.py does for OpenClaw sessions. Same principle.

---

### Challenge 6: The parallel execution model has a design smell.

**Current:** The orchestrator maintains testing agents as a "ratio" — a background ratio of N regression testers running independently. The dependency resolver is integrated into the orchestrator. The batch builder is also in the orchestrator. The orchestrator does too much.

**Refactored: Separate concerns into a proper pipeline.**

```
Scheduler      → what features are ready? in what order?
Dispatcher     → spawn agents for ready features
Pool           → manage active agents (capacity, backpressure)
ResultHandler  → process completions, update state
Testing        → optional parallel regression pipeline
```

```python
class Scheduler:
    """Pure function: features_state → work_items, ordered."""
    def get_ready(self, state: ProjectState) -> list[WorkItem]: ...

class AgentPool:
    """Manages running agents. Backpressure via asyncio.Semaphore."""
    def __init__(self, max_concurrent: int, plugin: AgentPlugin):
        self._sem = asyncio.Semaphore(max_concurrent)
    
    async def submit(self, work: WorkItem) -> AgentResult:
        async with self._sem:
            return await run_agent(work, self._plugin)

class Dispatcher:
    """Main loop: scheduler → pool → result_handler."""
    async def run(self):
        async with asyncio.TaskGroup() as tg:
            while not self.is_complete():
                for work in self.scheduler.get_ready(self.state):
                    tg.create_task(self.pool.submit(work))
                await asyncio.sleep(self.poll_interval)
```

`asyncio.Semaphore` replaces the entire `MAX_PARALLEL_AGENTS`, `MAX_TOTAL_AGENTS`, `_lock`, `running_coding_agents`, `running_testing_agents` dict infrastructure — which is 400+ lines in `parallel_orchestrator.py`.

---

## The Proposed New Architecture

```
autoforge2/
├── pyproject.toml              # uv-compatible, PyPI-publishable
├── autoforge2/
│   ├── cli.py                  # Typer CLI: init, run, serve, plugins
│   ├── state/
│   │   ├── service.py          # FastAPI: /features, /sessions, /events SSE
│   │   ├── models.py           # SQLAlchemy (unchanged schema)
│   │   └── scheduler.py        # Dependency-aware scheduling
│   ├── orchestrator/
│   │   ├── dispatcher.py       # asyncio TaskGroup dispatch loop
│   │   ├── pool.py             # asyncio.Semaphore agent pool
│   │   └── manifest.py         # Session manifest writer
│   ├── plugins/
│   │   ├── base.py             # AgentPlugin protocol
│   │   ├── coding.py           # Built-in coding plugin
│   │   ├── testing.py          # Built-in testing plugin
│   │   └── initializer.py      # Built-in initializer plugin
│   ├── skills/
│   │   ├── coding-agent/SKILL.md
│   │   ├── testing-agent/SKILL.md
│   │   └── initializer/SKILL.md
│   └── ui/                     # React UI (unchanged)
```

**What stays the same:**
- Claude Agent SDK as the LLM interface (your requirement, and the right call)
- SQLite for feature state persistence
- React UI (no reason to change it)
- Dependency graph + scheduling algorithm (solid logic, just needs extraction)
- Security hooks (good pattern)

**What changes:**
- Node.js → Python/uv CLI
- MCP-as-state → REST AgentStateService
- subprocess+threads → asyncio TaskGroup
- Hardcoded agent types → plugin entry points
- Cold sessions → session manifest hydration
- Monolithic orchestrator → Scheduler + Pool + Dispatcher

---

## The Real Question I'd Challenge You On

AutoForge's `parallel_orchestrator.py` is doing 5 jobs at once. The 1,000-line complexity isn't because the problem is hard — it's because the abstraction boundaries are wrong.

The `asyncio.Semaphore` + `TaskGroup` + plugin approach cuts it to ~200 lines with better correctness guarantees. The MCP-as-state anti-pattern explains why the MCP server restarts on every agent spawn (400ms startup cost per agent).

**The hardest challenge:** The session manifest approach changes the mental model from "agents discover state" to "state is pushed to agents." This requires the AgentStateService to know enough about feature context to write a useful manifest — which means it needs to track file changes, git state, and test results. That's more service logic, but it eliminates the "10-20 minutes on first run" problem entirely.

Is that tradeoff worth it? That's the architecture decision.

---

*Ready to build any of these. Starting point recommendation: Challenge 1 (uv/PyPI) + Challenge 2 (REST service) gives you the most leverage for the least risk. Challenges 3+6 (asyncio refactor) can follow once the API layer is stable.*
