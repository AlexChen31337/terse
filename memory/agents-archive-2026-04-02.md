# AGENTS.md Archive — 2026-04-02
# Content removed during file diet to reduce bootstrap injection from 97KB to ~40KB
# This content is searchable via memory_search

## Archived Sections

### Opus SWE-bench Eval (STOPPED)
Do NOT restart the Opus eval. Baseline is 64% Sonnet.

### Detailed Group Chat Rules
See SOUL.md for communication rules. Key: participate don't dominate, react like a human, know when to speak.

### Detailed Heartbeat Protocol
Default prompt: Read HEARTBEAT.md. Track checks in memory/heartbeat-state.json.
Heartbeat vs cron: heartbeat for batched checks with conversational context, cron for exact timing/isolation.
Things to check: emails, calendar, mentions, weather. Rotate 2-4x/day.
Proactive work: organize memory, check projects, update docs, commit changes.

### Gateway Config Incident (2026-02-21)
Sub-agent used config.apply with stale snapshot → deleted model definitions → 8+ crons failed.
Rule: ALWAYS config.patch for partial. NEVER config.apply with stale config.

### Credential Storage Rules (HL Key Corruption 2026-02-23)
decrypt.sh ran two backends, outputs concatenated into corrupted key.
Rule: validate decrypt output before writing. Use store_credential.sh.

### Infrastructure Diagnosis Rules
Check TOOLS.md for full specs before diagnosing. Don't report "insufficient X" without checking all specs (RAM + swap + storage).

### Detailed PBR Steps 2-4
Step 2 — Harness scaffold: scaffold.py creates AGENTS.md, docs/, scripts/agent-lint.sh, CI.
Step 3 — Docs first: PLAN.md, ARCHITECTURE.md before code.
Step 4 — Reviewer gates: cargo test/go test/npm test + agent-lint.sh + doc_garden.py. 90% coverage, zero lint errors.

### Sub-Agent Spawning Protocol (Detailed)
Use spawn_helper for model selection. Tier mapping: SIMPLE→qwen3.5:4b, MEDIUM→llama-3.3-70b, COMPLEX→sonnet, REASONING→kimi-k2, CRITICAL→opus.
Router v2.0 uses 15-dimension scoring — trust the output.

### ClawInfra Repo Standards
Production-grade: docs first, TDD, 90%+ coverage, CI green, type-safe, changelog, semver.

### Platform Formatting Rules
Discord/WhatsApp: no markdown tables, use bullet lists. Discord links: wrap in <>. WhatsApp: no headers, use bold.
