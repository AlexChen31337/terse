# systematic-debug

**Trigger:** Use when facing any technical failure — test failures, CI errors, build issues, unexpected behaviour, bugs, integration problems.

## The Iron Law

**NO FIXES WITHOUT ROOT CAUSE FIRST.**

If you haven't completed Phase 1, you cannot propose fixes. Symptom fixes are failure.

## Four Phases — Complete Each Before Proceeding

### Phase 1: Root Cause Investigation

Before ANY fix attempt:

1. **Read error messages completely** — stack traces, line numbers, exit codes, file paths. They often contain the exact solution.

2. **Reproduce consistently** — Can you trigger it reliably? If not, gather more data. Don't guess.

3. **Check recent changes** — `git diff`, recent commits, new deps, config changes.

4. **Multi-component systems** — Add diagnostic instrumentation at EACH layer boundary:
   ```bash
   # Example: CI pipeline debugging
   echo "=== Layer 1: env vars available ==="
   env | grep -E "KEY|TOKEN|SECRET" | sed 's/=.*/=REDACTED/'
   
   echo "=== Layer 2: config files present ==="
   ls -la .env* *.toml *.json 2>/dev/null
   
   echo "=== Layer 3: dependencies ==="
   cargo check 2>&1 | head -20  # or go mod verify, pip check
   
   echo "=== Layer 4: actual failure ==="
   cargo test 2>&1 | grep -E "FAILED|error\[" | head -20
   ```
   Run once to gather evidence → identify failing layer → investigate that layer.

5. **Trace data flow** — Where does the bad value originate? Trace backwards up the call stack to the source. Fix at source, not symptom.

### Phase 2: Pattern Analysis

- Find working examples of similar code in the same codebase
- Compare working vs broken — list EVERY difference, however small
- Read reference implementations completely (no skimming)
- Identify all dependencies and assumptions

### Phase 3: Hypothesis and Testing

- State ONE hypothesis clearly: "I think X is the root cause because Y"
- Make the SMALLEST possible change to test it — one variable at a time
- Did it work?
  - YES → Phase 4
  - NO → Form NEW hypothesis. Do NOT stack more fixes on top.

### Phase 4: Implementation

1. Write a failing test case first (reproduces the bug)
2. Implement the single fix addressing the root cause
3. Verify: test passes, no regressions
4. If fix doesn't work → return to Phase 1

**After 3+ failed fixes:** Stop. Question the architecture, not the symptoms. Discuss with Bowen before continuing.

## Alex-Specific Patterns

```bash
# CI failure investigation template
gh run list --limit 5  # Find failing run
gh run view <id> --log-failed  # Read full failure log

# Rust/Cargo
cargo test 2>&1 | grep -A 10 "FAILED"
cargo check 2>&1 | grep "error\["

# Go
go test ./... 2>&1 | grep -E "FAIL|panic"

# Python
pytest -x --tb=short 2>&1 | tail -30

# General: always read the FULL error before proposing anything
```

## Red Flags — Return to Phase 1

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- Making multiple changes at once
- Proposing solutions before tracing data flow
- "One more fix attempt" after 2+ failures
- Each fix reveals a NEW problem in a different place

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue seems simple" | Simple bugs have root causes too |
| "Emergency, no time" | Systematic is FASTER than thrash-and-guess |
| "I see the problem" | Seeing symptoms ≠ understanding root cause |
| "Multiple fixes save time" | Can't isolate what worked; creates new bugs |
| "Reference too long" | Partial understanding guarantees bugs |

**Source:** Adapted from obra/superpowers/systematic-debugging (skills.sh)
**Adapted:** 2026-03-02 — added Alex-specific commands for ClawInfra stack
