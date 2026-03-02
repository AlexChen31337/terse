# verification-gate

**Trigger:** Use when about to claim a task is complete, tests pass, a bug is fixed, a build succeeds, or any positive assertion about work state.

## The Iron Law

**NO COMPLETION CLAIM WITHOUT FRESH VERIFICATION EVIDENCE.**

If you haven't run the check in this exact message, you cannot claim it passes.

## Gate Function — Run Before Every Completion Claim

1. **IDENTIFY** — What command proves this claim?
2. **RUN** — Execute it fresh and complete (no stale output)
3. **READ** — Full output, check exit code, count failures
4. **VERIFY** — Does output confirm the claim?
   - NO → State actual status with evidence
   - YES → State claim WITH the evidence inline
5. **ONLY THEN** — Make the claim

## Claim → Required Evidence

| Claim | Required evidence |
|-------|------------------|
| Tests pass | `pytest` / `cargo test` / `go test` output: 0 failures |
| Linter clean | Linter output: 0 errors/warnings |
| Build succeeds | Build command: exit 0 |
| Bug fixed | Original symptom reproduced and now passes |
| Subagent completed | VCS diff shows actual changes |
| Requirements met | Line-by-line checklist verified |
| CI green | Fresh CI run link or local equivalent |

## Red Flags — STOP Immediately

- Using "should", "probably", "seems to", "looks like"
- Expressing satisfaction before verification ("Done!", "Perfect!", "Great!")
- About to commit/push/PR without running tests
- Trusting subagent success reports without independent check
- Relying on partial verification ("linter passed" ≠ build passes)
- "Just this once" thinking

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Agent said success" | Verify independently with `git diff` |
| "Linter passed" | Linter ≠ compiler ≠ tests |
| "I'm tired" | Exhaustion is not an excuse |
| "Partial check is enough" | Partial proves nothing |

## Alex-Specific Checkpoints

Before telling Bowen a task is done:
```bash
# Code tasks
git diff --stat HEAD~1  # Verify changes exist
cargo test 2>&1 | tail -5  # or pytest / go test

# Subagent tasks  
git log --oneline -3  # Did subagent actually commit?

# Config changes
openclaw doctor 2>&1 | grep -E "error|warning" | head -5

# Cron/infra changes
openclaw status 2>&1 | tail -10
```

**Source:** Adapted from obra/superpowers/verification-before-completion (skills.sh)
**Adapted:** 2026-03-02 — merged with existing VBR protocol in SOUL.md
