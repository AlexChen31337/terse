# ☀️ Morning Digest — Sunday, April 19, 2026

## 🚨 Urgent / Needs Immediate Attention

🐙 **[GITHUB]** security: audit + fix pallet-ibc-lite, pallet-anon-messaging, pallet-service-market
   🔗 https://api.github.com/repos/clawinfra/claw-chain/pulls/54

## 🐙 GitHub — 51 Items

### bowen31337/dataViz-agent
- ✍️ bug: notify-change route uses undefined permission 'embeddings:write' — always returns 403 [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/issues/58
- ✍️ feat(cost): Claude prompt prefix caching for schema + universal rules [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/issues/48
- ✍️ feat(observability): full pipeline tracing with Langfuse (schema_link → few_shot → generate → explain → execute) [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/issues/47
- ✍️ feat(observability): full pipeline Langfuse tracing (#47) [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/pulls/55
- ✍️ feat(cache): rule-versioned few-shot cache with automatic invalidation on rule change [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/issues/46
- ✍️ feat(cache): rule-versioned cache with automatic invalidation on rule change (#46) [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/pulls/54
- ✍️ feat(text-to-sql): query complexity router — model tier selection (#45) [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/pulls/53
- ✍️ feat(text-to-sql): column value sampling for enum resolution [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/issues/44
- ✍️ feat(text-to-sql): column value sampling for enum resolution (#44) [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/pulls/52
- ✍️ feat(text-to-sql): pre-execution LLM self-review gate (close semantic correctness gap) [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/issues/43
- ✍️ feat(text-to-sql): semantic few-shot retriever with masked question similarity [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/issues/42
- ✍️ feat(text-to-sql): semantic few-shot retriever with masked question similarity (#42) [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/pulls/50
- ✍️ feat(text-to-sql): semantic schema linker — embedding-based column selection [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/issues/41
- ✍️ feat(text-to-sql): semantic schema linker — embedding-based column selection (#41) [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/pulls/49
- ✍️ feat: LLM tracing — prompt snapshot, latency, and token usage per query [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/issues/25
- ✍️ feat: admin portal UI for query embeddings management [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/issues/22
- ✍️ perf: gate judgeResult behind LLM_JUDGE_ENABLED env var, default false [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/issues/12
- ✍️ bug: injectLimit appends LIMIT 200 to aggregation and GROUP BY queries incorrectly [author]
  🔗 https://api.github.com/repos/bowen31337/dataViz-agent/issues/11

### clawinfra/agent-tools
- 📌 #1 v0.1 Feature Roadmap — Agent Tool Registry Foundation [open_issue]
  🔗 https://github.com/clawinfra/agent-tools/issues/1

### clawinfra/claw-chain
- ✍️ fix(ci): remove invalid libp2p-tls self-patch [author]
  🔗 https://api.github.com/repos/clawinfra/claw-chain/pulls/58
- ✍️ fix(ci): format cargo-audit ignore list as comma-separated values [author]
  🔗 https://api.github.com/repos/clawinfra/claw-chain/pulls/56
- ✍️ security: audit + fix pallet-ibc-lite, pallet-anon-messaging, pallet-service-market [author]
  🔗 https://api.github.com/repos/clawinfra/claw-chain/pulls/54
- ✍️ feat: pallet-service-market v2 (#42) [author]
  🔗 https://api.github.com/repos/clawinfra/claw-chain/pulls/48
- ✍️ feat: pallet-ibc-lite — cross-chain messaging (#41) [author]
  🔗 https://api.github.com/repos/clawinfra/claw-chain/pulls/46
- ✍️ feat: OpenClaw integration — framework binding (#36) [author]
  🔗 https://api.github.com/repos/clawinfra/claw-chain/pulls/45
- ✍️ feat: testnet faucet service [author]
  🔗 https://api.github.com/repos/clawinfra/claw-chain/pulls/39
- 👤 [IMPL] Substrate runtime workspace setup [mention]
  🔗 https://api.github.com/repos/clawinfra/claw-chain/issues/27
- 👤 feat: Substrate node implementation [mention]
  🔗 https://api.github.com/repos/clawinfra/claw-chain/pulls/26
- 📌 #100 RUSTSEC-2026-0099: Name constraints were accepted for certificates asserting a wildcard name [open_issue]
  🔗 https://github.com/clawinfra/claw-chain/issues/100
- 📌 #99 RUSTSEC-2026-0098: Name constraints for URI names were incorrectly accepted [open_issue]
  🔗 https://github.com/clawinfra/claw-chain/issues/99
- 📌 #97 RUSTSEC-2026-0098: Name constraints for URI names were incorrectly accepted [open_issue]
  🔗 https://github.com/clawinfra/claw-chain/issues/97
- 📌 #96 RUSTSEC-2025-0161: libsecp256k1 is unmaintained [open_issue]
  🔗 https://github.com/clawinfra/claw-chain/issues/96
- 📌 #94 chore: migrate wasmtime 28.x → 30.x (RUSTSEC-2026-0085 through 0096) [open_issue]
  🔗 https://github.com/clawinfra/claw-chain/issues/94

### clawinfra/claw-forge
- ✍️ bug: hard-killed runs leave commits stranded on orphaned worktree branches [author]
  🔗 https://api.github.com/repos/clawinfra/claw-forge/issues/19
- ✍️ feat: Anthropic harness improvements — context resets, adversarial evaluator, strategic pivot [author]
  🔗 https://api.github.com/repos/clawinfra/claw-forge/issues/17
- ✍️ feat(harness): HandoffArtifact module, README docs, patterns guide — closes #17 [author]
  🔗 https://api.github.com/repos/clawinfra/claw-forge/pulls/18

### clawinfra/evoclaw
- ✍️ feat: multi-chain CLI (#18) [author]
  🔗 https://api.github.com/repos/clawinfra/evoclaw/pulls/19
- ✍️ Sync master to main: Core skills + test coverage improvements [author]
  🔗 https://api.github.com/repos/clawinfra/evoclaw/pulls/7
- ✍️ Add core skills infrastructure: tiered-memory, intelligent-router, agent-self-governance [author]
  🔗 https://api.github.com/repos/clawinfra/evoclaw/pulls/6
- ✍️ fix(mqtt): Orchestrator → Edge Agent Message Format Mismatch [author]
  🔗 https://api.github.com/repos/clawinfra/evoclaw/issues/5
- ✍️ Bug: selectAgent() routing is non-deterministic due to Go map iteration [author]
  🔗 https://api.github.com/repos/clawinfra/evoclaw/issues/4
- ✍️ fix(mqtt): prevent race condition on channel closure [author]
  🔗 https://api.github.com/repos/clawinfra/evoclaw/pulls/3
- 📌 #46 feat: SKILLRL v2 — persistent trajectories, reward shaping, embedding similarity [open_issue]
  🔗 https://github.com/clawinfra/evoclaw/issues/46
- 📌 #45 feat: OpenTelemetry observability suite [open_issue]
  🔗 https://github.com/clawinfra/evoclaw/issues/45
- 📌 #44 feat: multi-agent collaboration protocol [open_issue]
  🔗 https://github.com/clawinfra/evoclaw/issues/44
- 📌 #41 feat: production readiness — health checks, graceful shutdown, K8s [open_issue]
  🔗 https://github.com/clawinfra/evoclaw/issues/41
- 📌 #40 feat: pluggable context engine via abstract base class [open_issue]
  🔗 https://github.com/clawinfra/evoclaw/issues/40

### illbnm/homelab-stack
- ✍️ feat(tests): automated integration test suite for all stacks (Closes #14) [author]
  🔗 https://api.github.com/repos/illbnm/homelab-stack/pulls/261
- ✍️ feat: Database Layer + Backup/DR + Notifications + Integration Tests [author]
  🔗 https://api.github.com/repos/illbnm/homelab-stack/pulls/53

### openclaw/openclaw
- ✍️ feat: Native RSI (Recursive Self-Improvement) hooks in agent runtime [author]
  🔗 https://api.github.com/repos/openclaw/openclaw/issues/23270
- ✍️ Proposal: Add PageIndex as optional memory backend (alternative to vector embeddings) [author]
  🔗 https://api.github.com/repos/openclaw/openclaw/issues/17919

---
📊 Total: 51 items | Actionable: 40 | Urgent: 1
Generated: 22:40 UTC+11:00