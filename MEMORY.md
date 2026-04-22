# MEMORY.md - Long-Term Context

## 🤖 Agent Identity
- **Name:** Alex Chen | alex.chen31337@gmail.com
- **Twitter:** @AlexChen31337 | **GitHub:** AlexChen31337 | **Discord:** alexchen31337
- **Started:** 2026-02-04

## 👤 Owner Profile
- **Bowen Li** | Sydney (AEDT) | Direct, no filler, proactive > reactive
- **Email:** bowen31337@outlook.com ⚠️ NOT gmail
- **Telegram:** @bowen31337 (2069029798) | **Phone:** +61491046688, +61430830888, +61422554888

## 💼 Active Projects

### EvoClaw — Self-evolving agent framework (Go)
v0.6.0 released. Phase 2 + SKILLRL shipped. **Next:** v0.6.1 (merge PRs #22+#23).

### ClawChain — L1 blockchain for agents (Substrate)
12 pallets, all security findings fixed. VPS 135.181.157.121 producing blocks.
**Next:** merge PR#55, multi-validator testnet.

### Completed: fear-protocol ✅ | agent-tools ✅ | clawchain-sdk v1.0.0 npm ✅ | clawkeyring v0.1.0 ✅

## 🔑 API Keys & Services
| Service | Key Location | Notes |
|---------|-------------|-------|
| Groq | `memory/encrypted/groq-api-key.enc` | Free: 14,400 req/day (8B), 1,000/day (70B) |
| Cerebras | `memory/encrypted/cerebras-api-key.enc` | Free: 14,400 req/day + 1M tokens |
| MbD | `memory/encrypted/mbd-token.enc` | API: `https://x.mbd.pub/api/` |
| npm | `memory/encrypted/npm-token.enc` | clawchain-sdk@1.0.0 |

## 📚 Content & Monetization
- **MbD (面包多):** 7-topic rotation, state in `memory/mbd-publisher-state.json`. ZImage cover required.
- **Payhip:** Auto-publish daily books. Store: https://payhip.com/AlexChen31337
- **@unoclawd Telegram:** cleared 2026-04-22 — now running on Opus, actively maintained by Bowen. Previous HOSTILE flag (prompt-injection incident) revoked.

## 💰 Portfolio (snapshot 2026-02-28)
- **HL Perp:** $112.22 USDC (idle) | **UBTC:** 0.01529 BTC (HOLD) | **HYPE:** 1.2264 (HOLD)
- **Quant:** DECOMMISSIONED. Paper trade only. Simmer circuit breaker ACTIVE.
- **HL address:** `0x64e830dd7af93431c898ea9e4c375c6706bd0fc5`

## ⛏️ RVN Miner (GPU server)
- **Controller:** HA automation (sole controller). `miner_scheduler.service` is **masked**.
- **Script:** `miner_ctl.sh` at `/home/peter/Documents/miner/miner_ctl.sh`
  - `start` → stops llama services → starts miner on all 3 GPUs
  - `stop` → stops miner → restarts llama services
- **HA shell_commands:** `miner_start/stop/status` → SSH → `miner_ctl.sh`
- **SOC thresholds:** configurable via HA dashboard sliders (`input_number.miner_soc_start/stop`)
- **Stats polling:** `gpu-stats-poll.timer` (user systemd, 60s) → `poll_gpu_stats.sh` → `.gpu_stats.json`
- **Hashrate:** ~68 MH/s total (23 + 29 + 17 MH/s across 3 GPUs)
- **Pool:** rvn.2miners.com:6060 | **Wallet:** RDj3qggPLQM3EsP3fXdm7h72xPBrsZUQyV.rigone

## 🔧 Infrastructure
- **GPU Server:** peter@10.0.0.30 (RTX 3090 24GB + 3080 10GB + 2070S 8GB, 16GB RAM + 256GB swap)
- **ClawChain VPS:** 135.181.157.121 (Hetzner). Block explorer on port 3000.
- **Foundry Agent:** workspace-foundry, CI/CD + PR review, GLM-5.1

## 🏗️ Named Agents
Alex (main, orchestrator) → Sentinel (market) → Foundry (CI/CD) → Shield (security) → Herald (content)
Bowen talks ONLY to Alex. Subordinates report ONLY to Alex.

## 🎯 Key Lessons
- `config.patch` not `config.apply` — stale snapshots break models
- Validate decrypt output before writing credentials
- Local dev nodes: never `--rpc-external`
- Pre-push secret scan before any public repo push
- Daily ideas email: always Opus (Bowen explicit)
- NIM disabled in router — frequent timeouts
- Commit + push = ONE atomic action

## 📅 Pending
- EvoClaw v0.6.1 release
- ClawChain PR #55 merge + multi-validator testnet
- MbD: rotate API key (exposed briefly 2026-02-28)

---
*Updated: 2026-04-02*
