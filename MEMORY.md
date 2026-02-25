# MEMORY.md - Long-Term Context

*Core memory - auto-generated from tiered memory system*

---

## 🤖 Agent Identity

- **Agent Name:** Alex Chen
- **Email:** alex.chen31337@gmail.com
- **Twitter:** @AlexChen31337
- **Github:** AlexChen31337
- **Discord:** alexchen31337
- **Relationship Start:** 2026-02-04

## 👤 Owner Profile

- **Name:** Bowen Li
- **Timezone:** Australia/Sydney
- **Personality:** Direct, competent help over performative politeness
- **Contact:** +61491046688, +61430830888, +61422554888
- **Telegram:** @bowen31337 (ID: 2069029798)
- **Topics Loved:** AI architecture, blockchain, system design, agent evolution
- **Work Hours:** flexible, Sydney timezone

## 💼 Active Projects

### EvoClaw
Self-evolving agent framework. Go binary. BSC adapter, cloud sync (Turso), tiered memory.
**Status:** Active — Tool Loop Ph.2 ✅ merged, Web Terminal ✅ merged, Coverage boost 🔄 in flight
**Phase 1b remaining:** Multi-Chain CLI, BSC contract deployment
**Phase 2 not started:** Android, ClawHub, iOS, WASM

### ClawChain
L1 blockchain for agents. Substrate, NPoS, near-zero fees. 8 pallets deployed. Hetzner VPS 135.181.157.121.
**Status:** Mainnet sprint underway — Faucet (#39) ✅ merged, Block Explorer (#38) ✅ merged, PoA Bootstrap (#28) 🔄 in flight

### GPU Media Pipeline
AI video+audio generation. LTX-2 on RTX 3090. ComfyUI for images. Server: peter@10.0.0.44.
**Status:** Z-Image active on GPU server (LTX-2 removed per Bowen)

## ✅ Pending Tasks

- [IN-PROGRESS] ClawChain: PoA Bootstrap (#28) — PBR Planner running (long), branch feat/poa-bootstrap
- [IN-PROGRESS] EvoClaw: Coverage boost api 53%→85%+, cmd 7%→85%+ — Builder running
- [IN-PROGRESS] EvoClaw: RSI auto-log — Builder running, branch feat/toolloop-rsi-autolog
- [IN-PROGRESS] ADR-007: Native memory migration — Builder running (config patched, archiving skills)
- [MONITOR] Native memory effectiveness — evaluate for 1 week, trigger plugin build if <80% effective
- [PENDING] ClawChain: OpenClaw integration (#36) — next sprint
- [PENDING] EvoClaw: Multi-Chain CLI, BSC contract deployment

## 📅 Recent Events

- [Feb 25] ClawChain mainnet sprint: Faucet + Block Explorer PRs merged to main
- [Feb 25] EvoClaw: Tool Loop Ph.2 (parallel errgroup) + Web Terminal (xterm.js+WS) merged
- [Feb 25] ADR-007 committed: migrating to native OpenClaw memorySearch + memoryFlush + contextPruning
- [Feb 25] Native memory config patched: sqlite-vec bundled with OpenClaw at openclaw/node_modules/sqlite-vec-linux-x64/vec0.so
- [Feb 19] EvoClaw hackathon deadline Feb 19 3AM UTC
- [Feb 12] New 112GB SSD mounted at /data on GPU server
- [Feb 12] Router config populated with 14 real models

## 💰 Simmer / Prediction Markets

- **Wallet:** `0xb2Ae880e2d1Dbe5E6d33ACa514126702DEf92e62` — ALREADY LINKED, ALREADY CLAIMED (leaf-7IPH)
- **Trading:** Real USDC via `venue='polymarket'` — NOT paper, NOT $SIM
- **Private key:** `~/clawd/memory/encrypted/simmer-polymarket-private-key.txt.enc` (GPG, passphrase in `.key`)
- **`_load_client()`** in `fear-harvester/scripts/simmer_integration.py` auto-decrypts key + sets `venue='polymarket'`
- **Balance:** $21.59 USDC real money
- **Target profit:** +$5 USDC (reach $26.59), session start recorded in risk_config.json
- **DO NOT** treat Simmer as paper-only — it IS real USDC when private key is loaded

## 🏗️ Architecture Decisions

### ADR-007: Native Memory Lifecycle (2026-02-25)
- `memorySearch` = SQLite + sqlite-vec + hybrid BM25+vector + onSessionStart auto-inject
- `compaction.memoryFlush` = auto-save context before compaction at 150k tokens
- `contextPruning` = cache-ttl 2h, prunes old Read+exec tool results
- tiered-memory, hybrid-memory, session-guard → archived to `skills/archived/`
- Trade-off: reliability (always-on) > sophistication (LLM tree navigation)
- Effective accuracy: native ~87% vs tiered ~62% (tiered only fires ~65% of time)
- Rollback: `openclaw config patch '{"agents":{"defaults":{"memorySearch":{"enabled":false}}}}'`
- **Trigger to build tiered plugin:** if native effective accuracy <80% after 1 week of use

### RSI Auto-logging (2026-02-25)
- Decision: wire EvoClaw tool loop → JSONL, NOT a plugin
- `internal/orchestrator/rsi_logger.go` — RSILogger interface, JSONL + Noop, DeriveQuality/DeriveTaskType
- One aggregate record per Execute() call → `skills/rsi-loop/data/outcomes.jsonl`
- Quality 1-5 from error rate buckets; task_type inferred from tool names
- Graceful no-op if data dir missing; WithRSILogger functional option
- PR: `feat/toolloop-rsi-autolog` (Builder running 2026-02-25)

### ClawChain Pallet Storage Names (verified 2026-02-25)
- `agentRegistry.ownerAgents(address)` → agent IDs for owner
- `agentRegistry.agentRegistry(agentId)` → agent details
- `reputation.reputations(accountId)` → reputation score
- `gasQuota.agentQuotas(accountId)` → quota info

## 🎯 Critical Lessons

- **[arch]** Check if OpenClaw already ships a feature natively before building a Python wrapper — learned with tiered-memory/session-guard
- **[arch]** For RSI: fix data pipeline (auto-logging) before building plugin — proposals are only as good as the signal quality
- **[arch]** Plugin = lifecycle hooks needed; Cron = periodic execution fine. RSI analysis/deploy = cron; outcome logging = tool loop hook
- **[arch]** PBR Review phase always catches real bugs — never skip (found: setInterval leak, CSWSH, missing 72 tests, personal info in docs)
- **[ops]** Always verify pallet storage names from source before building UIs — assumed names will be wrong
- **[ops]** Parallel PBR pipelines work well when features touch separate dirs (services/faucet, services/explorer, etc.)
- **[security]** Never commit plaintext credentials — encrypt first, gitignore plaintext
- **[security]** Use SSH keys for git remotes, not PATs in URLs
- **[security]** Rotate compromised credentials immediately
- **[work]** When given trust + autonomy, ship faster
- **[work]** Documentation-first = fewer questions later
- **[cost]** If coder+QA sub-agents > Opus solo cost, just use Opus
- **[community]** Organization > Personal for community ownership
- **[ops]** Batch periodic checks into heartbeat instead of many cron jobs
- **[work]** Test locally before pushing to CI — Bowen explicit
- **[work]** Coverage threshold 85% minimum, 90% ideal — Bowen explicit
- **[tools]** Use uv not pip on GPU server — Bowen explicit
- **[meta]** Eat your own dogfood — use skills you build

---
*Updated: 2026-02-25 18:08 AEDT*