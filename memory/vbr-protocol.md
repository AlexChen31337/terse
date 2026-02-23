# VBR (Verify Before Reporting) Protocol

**Created:** 2026-02-23 11:30 PM
**Purpose:** Prevent repeated VBR violations (push-without-local-test, claiming done without verification)

## Core Rule

**Never claim a task is complete without verification.**

### Before Saying "Done"

1. **Code changes:** Run tests locally (`pytest`, `ruff`, `cargo test`, etc.)
2. **CI setup:** Verify it actually runs with a sample commit
3. **Bug fixes:** Reproduce the bug first, then verify the fix
4. **Cron jobs:** Check at least one successful run
5. **External actions:** Confirm the result (email sent, tweet posted, etc.)

### Red Flags (Stop and Verify)

- "I think it's working" → **Not acceptable. Test it.**
- "Should be fine now" → **Not acceptable. Verify.**
- "CI is set up" → **Did you test it? Push a commit?**
- "Fixed the bug" → **Did you reproduce it first?**

### Consequences

- **VBR violation** = automatic quality score ≤ 2
- **Repeated VBR violations** = RSI pattern: "push-without-local-test"
- **Impact:** 75% failure rate, lost trust, wasted time

## Examples

### ❌ Wrong
```
"I've set up CI for the repo. Done."
[Reality: Never tested, CI doesn't actually run]
```

### ✅ Right
```
"I've set up CI for the repo. Let me verify:
1. Created .github/workflows/ci.yml ✅
2. Triggered test run via sample commit ✅
3. All tests passed: https://github.com/.../actions/runs/123 ✅
Done. Verified."
```

## Integration with RSI

Every task outcome log MUST include:
- **Verification steps taken**
- **Evidence of completion** (logs, URLs, screenshots)
- **If no verification possible** → Mark as "incomplete", not "done"

## Auto-Checklist (Mental)

Before declaring done, ask:
- [ ] Did I run this locally?
- [ ] Did I see it work with my own eyes?
- [ ] Can I provide evidence?
- [ ] Would I bet $100 this works?

If any answer is NO → **Not done. Go verify.**

---

**Pattern this addresses:** unknown-none (VBR violations, timeouts, unverified claims)
**Failure rate:** 75% → Target: <10%
**Expected improvement:** Quality score 2.12 → 4.0+
