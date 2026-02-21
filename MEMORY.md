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

## 🔑 Critical Infrastructure Notes
- **HL Wallet:** `0x64e830dd7aF93431C898eA9e4C375C6706bd0Fc5` | key at `memory/encrypted/hl-private-key.txt.enc`
- **HL Spot:** currently empty (~$0 USDC); Perp: ~$106 | FearHarvester in PAPER mode until funded
- **Sub-agent Opus:** NOT available for sessions_spawn — only proxy-1 crons; use Sonnet 4.6 for all coding sub-agents
- **config.apply is banned for sub-agents** — always `config.patch`; see AGENTS.md Gateway Config Rules

## 💼 Active Projects

### EvoClaw
Self-evolving agent framework. Go binary. BSC adapter, cloud sync (Turso), tiered memory. Hackathon deadline Feb 19.
**Status:** Active — CI coverage boost (74% → 85%), release prep

### ClawChain
L1 blockchain for agents. Substrate, NPoS, near-zero fees. 8 pallets deployed. Hetzner VPS 135.181.157.121.
**Status:** Testnet live at testnet.clawchain.win

### GPU Media Pipeline
AI video+audio generation. LTX-2 on RTX 3090. ComfyUI for images. Server: peter@10.0.0.44.
**Status:** LTX-2 setup in progress, blocked on Gemma 3 download

### WhaleWatch CLI
Agent-native whale wallet tracker. CLI + OpenClaw skill. ETH+BTC flows, JSONL streaming, Simmer auto-bet integration.
**Repo:** `github.com/clawinfra/whalecli` | **Status:** Planner running (Sonnet 4.6 fallback)

### Guardrail Skill
3rd-party asset vetting pipeline. Intake→scan→Telegram review→merge. 38 tests, 93% coverage.
**Status:** Phase 1 done ✅ | Phase 2 (Docker sandbox) next → EvoMap registration unlocks after

## ✅ Pending Tasks

- [PENDING] Bowen fund HL spot account → switch FearHarvester to --live (reminder set 10am Feb 22)
- [PENDING] Guardrail Phase 2: Docker sandbox runner
- [IN-PROGRESS] WhaleWatch CLI: Planner → Builder → Reviewer pipeline running
- [PENDING] RSI 3 proposals awaiting review: `uv run python skills/rsi-loop/scripts/synthesizer.py list`
- [PENDING] Quant SOUL.md update (still points to old signals.py, needs run_harvester.py)
- [PENDING] Bird CLI reinstall for KOL monitoring
- [BLOCKED] LTX-2 Gemma 3 text encoder (needs HF auth)
- [PENDING] EvoMap Hub registration (blocked on Guardrail Phase 2)

## 📅 Recent Events

- [Feb 19] EvoClaw hackathon deadline Feb 19 3AM UTC
- [Feb 12] New 112GB SSD mounted at /data on GPU server
- [Feb 12] Router config populated with 14 real models

## 🎯 Critical Lessons

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
- **[ops]** `config.apply` from sub-agents destroys model definitions — always `config.patch`
- **[ops]** `openclaw doctor` is a safeguard, not a threat — it fixed the proxy-4/6 outage
- **[security]** 3rd-party skills need guardrail vetting before install — never auto-apply external code
- **[arch]** Agent identity (Alex) ≠ marketplace identity (EvoClaw Hub) — keep them separate
- **[cost]** Opus 4.6 not available for sessions_spawn — use Sonnet 4.6 for all coding sub-agents

---
*Updated: 2026-02-22 09:47*