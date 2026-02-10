# MEMORY.md - Long-Term Context

*Curated memory - auto-generated from tiered memory system*

---

## 🧑 About Bowen

- **Timezone:** Australia/Sydney
- **Style:** Direct, competent help over performative politeness
- **Contact:** +61491046688, +61430830888, +61422554888
- **Telegram:** @bowen31337 (ID: 2069029798)

## 🤖 Agent Identity

- **Name:** Alex Chen
- **Email:** alex.chen31337@gmail.com
- **Twitter:** @AlexChen31337
- **Github:** AlexChen31337
- **Discord:** alexchen31337

## 💼 Active Projects

### ClawChain
**Status:** Architecture phase, community recruitment
Layer 1 blockchain built by agents, for agents. Substrate framework, NPoS consensus, near-zero fees. Repo: github.com/clawinfra/claw-chain. $CLAW token: 1B supply, 40% contributor airdrop.

### EvoClaw
**Status:** Active - BSC on-chain + tiered memory
Self-evolving agent framework. Go binary (7.2MB). BSC adapter, cloud sync (Turso), tiered memory system. Hackathon: Good Vibes Only OpenClaw Edition, $100K, deadline Feb 19.

## 🎯 Key Learnings

- Never commit plaintext credentials — encrypt first, gitignore plaintext filenames
- Use SSH keys for git remotes, not PATs in URLs
- Rotate compromised credentials immediately
- When given trust + autonomy, ship faster
- Documentation-first = fewer questions later
- Parallel development = compound progress
- If coder+QA sub-agents > Opus solo cost, just use Opus
- Organization > Personal for community ownership
- Transparent contribution scoring builds trust in open source
- Batch periodic checks into heartbeat instead of many cron jobs

## 📝 Recent Context

### projects/evoclaw
- [Feb 09] EvoClaw hackathon deadline is Feb 19 3AM UTC, Good Vibes Only OpenClaw Edition on BNBChain

### technical/security
- [Feb 09] All 12 credential files encrypted AES-256-CBC in memory/encrypted/*.enc, decrypt with memory/decrypt.sh
- [Feb 09] Gmail app password: AlexClaw2 (rotated Feb 8). 2FA needs Bowen's TOTP for browser login.
- [Feb 09] SSH key for AlexChen31337: ~/.ssh/id_ed25519_alexchen (alias: github-alexchen)

### projects/evoclaw/bsc
- [Feb 09] AgentRegistry deployed to BSC Testnet! Contract: 0xD20522b083ea53E1B34fBed018bF1eCF8670EaCf. Deployer: 0xcf7C6bd4062961882Ca4219ACD7f45ff651D927C. First agent registered on-chain. Explorer: https://testnet.bscscan.com/address/0xD20522b083ea53E1B34fBed018bF1eCF8670EaCf

### projects/clawchain
- [Feb 09] ClawChain testnet deployed to Hetzner VPS 135.181.157.121. Binary 62MB ARM64. Cloudflare tunnel moved from Dell to VPS. Public endpoint: https://testnet.clawchain.win (wss://testnet.clawchain.win). Frankfurt PoPs. 8 pallets: staking, session, treasury, sudo, task-market, reputation, agent-registry, claw-token.
- [Feb 09] ClawChain staking resolved: sp-staking v42.1 fixes version conflicts. Added pallet-staking, pallet-session, pallet-treasury, pallet-sudo, pallet-task-market, pallet-reputation. 54 tests pass. Building release binary.
- [Feb 09] ClawChain dev testnet running on Dell: ws://localhost:9944, PID at /tmp/clawchain-node.pid, producing blocks every 6s, 6 pre-funded accounts with ~55.5M CLAW each

### technical
- [Feb 09] Hetzner VPS: 135.181.157.121, root, aarch64, 2 cores, 4GB RAM, 38GB disk, Ubuntu 24.04. SSH key added. Password: encrypted in hetzner-credentials.json.enc. Purpose: ClawChain testnet. Cloudflare tunnel running on Dell (PID in /tmp/cloudflared.pid).

### lessons/cost
- [Feb 09] Non-coding tasks use GLM-4.5-Air (~$0.005/run). Complex coding uses Opus. If coder+QA > Opus solo, just use Opus.

---
*Auto-generated: 2026-02-10 22:15 | Warm: 25 facts | Tree: 20 nodes*
*Review frequency: Auto-rebuilt each session*