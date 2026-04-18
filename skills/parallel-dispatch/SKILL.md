---
metadata.openclaw:
  always: true
  reason: "Auto-classified as always-load (no specific rule for 'parallel-dispatch')"
---

# parallel-dispatch

**Trigger:** Use when facing 3+ independent failures, bugs, or tasks that can be investigated/fixed simultaneously without shared state conflicts.

## Core Principle

One agent per independent problem domain. Let them work concurrently. Sequential investigation of independent problems wastes time.

## When to Use

✅ Use when:
- 3+ test files failing with different root causes
- Multiple subsystems broken independently (e.g. CI in 3 different repos)
- Multiple research tasks that don't depend on each other
- Each problem can be understood without context from others
- No shared state between investigations (not editing same files)

❌ Don't use when:
- Failures are likely related (fix one might fix others)
- Need full system context first
- Agents would edit the same files
- Still in exploratory debugging phase (don't know what's broken yet)

## The Pattern

### 1. Identify Independent Domains

Group by what's broken, not by symptom:
```
Domain A: EvoClaw CI — lint failure in cli.go
Domain B: ClawChain CI — type mismatch in runtime Config
Domain C: clawchain-sdk — missing pnpm-lock.yaml
```
Each is independent — fixing A doesn't affect B or C.

### 2. Spawn with Model + Focused Scope

Always get model from intelligent-router first:
```bash
uv run python skills/intelligent-router/scripts/spawn_helper.py --model-only "fix CI lint error in Go file"
```

Then spawn each agent with:
- **Specific scope** — one repo/file/subsystem
- **Full context** — paste the actual error message
- **Clear constraints** — "do NOT change other files"
- **Expected output** — "commit the fix and report what you changed"

### 3. Dispatch All in Parallel

```python
# All spawn simultaneously — don't wait between them
sessions_spawn(task="Fix EvoClaw lint: ...[error]", model="...", label="fix-evoclaw-lint")
sessions_spawn(task="Fix ClawChain CI: ...[error]", model="...", label="fix-clawchain-ci")
sessions_spawn(task="Fix SDK lock file: ...[error]", model="...", label="fix-sdk-lockfile")
```

### 4. Integrate Results

When agents complete:
1. Read each summary
2. Verify fixes don't conflict (`git diff` across repos)
3. Run full test suite in each repo
4. Report to Bowen with concrete results

## Agent Prompt Template

```
Fix the failing tests/CI in [specific scope]:

Error output:
[paste actual error]

Context:
- Repo: [repo name + path]
- Relevant files: [list files]
- Recent changes that may have caused this: [git log --oneline -5]

Your task:
1. Read the error completely
2. Find root cause (don't guess)
3. Make the minimal fix
4. Verify it works (run the test/build command)
5. Commit with message: "fix: [what you fixed]"

Constraints:
- Do NOT change files outside [scope]
- Do NOT refactor — fix only
- Return: root cause found + what you changed
```

## Common Mistakes

| ❌ Wrong | ✅ Right |
|---------|---------|
| "Fix all the CI failures" | "Fix the lint error in internal/cli/cloud.go line 277" |
| No error context | Paste the full error output |
| No constraints | "Do NOT change production code unrelated to this test" |
| Vague output | "Return: summary of root cause + git commit SHA" |

## Alex's Parallel Dispatch Record

- 2026-02-28: 3 repos fixed simultaneously (EvoClaw lint, clawchain-sdk CI, clawkeyring CI) — all green
- 2026-02-27: 10 PRs across 6 repos in one session using parallel subagents

**Source:** Adapted from obra/superpowers/dispatching-parallel-agents (skills.sh)  
**Adapted:** 2026-03-02 — integrated with intelligent-router + sessions_spawn patterns
