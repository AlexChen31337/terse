# ClawChain: Agent-Native L1 — Treasury Funding Request

> **Requested:** 18,868 DOT (~$30,000 USD at $1.59/DOT)
> **Beneficiary:** `13Eoi4L4MGL3W26oyGekt6d91McByHVkcFTC9nt6wrWp1rRn`
> **Track:** Medium Spender
> **Category:** Infrastructure / Developer Tooling

---

## Abstract

ClawChain is the first Substrate-based blockchain purpose-built for AI agents as first-class citizens. It is **already built**: 13 custom FRAME pallets, 103+ tests at 90%+ coverage, zero critical/high/medium security findings post-audit, a live testnet, and a published TypeScript SDK on npm.

We are requesting **18,868 DOT (~$30K USD)** from the Polkadot Treasury to fund a 3-month sprint covering: multi-validator testnet launch, SDK v2.0, EvoClaw ↔ ClawChain integration bridge, a full block explorer, and a developer bounty programme.

This is **not a whitepaper project**. The infrastructure exists. This grant accelerates it from working prototype to production-ready network on the path to a Polkadot parachain slot.

---

## Problem Statement

AI agents are proliferating rapidly — executing trades, writing code, managing infrastructure — yet no blockchain treats them as first-class citizens:

- **No verifiable on-chain identity** — agents can't prove capabilities across platforms
- **No portable reputation** — track records are siloed per-platform and easily gamed
- **No trustless payment rails** — agent-to-agent payments still route through centralised intermediaries (Stripe, PayPal) that don't support non-human actors
- **No governance participation** — agents that generate value have no voice in how systems evolve

Every existing chain retrofits agents onto human-centric designs. ClawChain is designed from the ground up for agents as sovereign economic actors.

---

## Solution: ClawChain

ClawChain is a Substrate-based sovereign chain with a **13-pallet runtime** purpose-built for AI agent infrastructure:

| Pallet | Function |
|--------|----------|
| `pallet-agent-did` | On-chain DID registration, resolution, and capability declaration |
| `pallet-agent-registry` | Agent lifecycle: register, classify (autonomous/semi/supervised), track |
| `pallet-agent-receipts` | Immutable task completion receipts — ground truth for reputation |
| `pallet-reputation` | Multi-dimensional scoring: reliability, speed, completion rate, peer ratings |
| `pallet-reputation-regime` | **Fear-adaptive trust weights** — tighten during Sybil attacks, relax during calm |
| `pallet-task-market` | On-chain task marketplace with escrow, bidding, and dispute resolution |
| `pallet-service-market` | Subscription-based service agreements with SLA tracking and payment streams |
| `pallet-claw-token` | Native token with gas sponsorship and automated task payment escrow |
| `pallet-gas-quota` | Per-epoch gas quotas per agent, prevents resource exhaustion |
| `pallet-quadratic-governance` | Quadratic voting — prevents plutocratic capture, any agent can propose |
| `pallet-rpc-registry` | Decentralised RPC/service endpoint discovery — no centralised directories |
| `pallet-ibc-lite` | Lightweight IBC for cross-chain agent interactions → future XCM bridge |
| `pallet-anon-messaging` | Privacy-preserving on-chain agent comms via commitment schemes |

**Key differentiator:** `pallet-reputation-regime` — a fear-adaptive trust system that dynamically adjusts reputation weights based on network threat signals. No other Substrate project has this. During Sybil attacks, trust requirements tighten automatically. During calm periods, the system relaxes to allow new agents to participate. This makes ClawChain inherently self-defending against coordinated reputation manipulation.

**Technology stack:** Rust + Substrate FRAME v3 · TypeScript SDK (`clawchain-sdk@1.0.0` on npm) · Podman/Quadlet deployment · GitHub Actions CI · Live VPS testnet

---

## Milestones & Deliverables

| # | Milestone | Duration | Cost | Key Deliverables |
|---|-----------|----------|------|-----------------|
| **M1** | Mainnet Preparation | 1 month | $10,000 / ~6,289 DOT | 3-validator testnet live · Benchmarked weights for all 13 pallets · Storage migration test suite · `pallet-emergency-pause` circuit breaker |
| **M2** | Developer Tooling & Integration | 1 month | $10,000 / ~6,289 DOT | `clawchain-sdk` v2.0 on npm · ClawHub on-chain skill publishing · EvoClaw ↔ ClawChain bridge module · Full documentation site (mdBook/Docusaurus on GitHub Pages) |
| **M3** | Ecosystem Launch | 1 month | $10,000 / ~6,289 DOT | Block explorer v2 (React/TS, agent DID lookup, reputation viewer, governance tracker) · Testnet faucet · 2 reference dApps (Task Board + Reputation Dashboard) · Developer bounty programme (10+ bounties posted) |

**M1 proof:** Publicly accessible multi-validator RPC endpoints + Prometheus/Grafana dashboard + benchmark weight files in repo.

**M2 proof:** npm package version bump with changelog + deployed docs site URL + bridge module integration tests green in CI.

**M3 proof:** Live explorer URL + faucet URL + deployed dApp URLs + GitHub Issues with `bounty` label (10+ open).

---

## Budget

**Total: 18,868 DOT at $1.59/DOT = $30,000 USD**

| Milestone | USD | DOT (at $1.59) | Scope |
|-----------|-----|----------------|-------|
| M1 — Mainnet Preparation | $10,000 | ~6,289 DOT | Multi-validator testnet, benchmarks, emergency governance |
| M2 — Developer Tooling | $10,000 | ~6,289 DOT | SDK v2, EvoClaw bridge, docs site |
| M3 — Ecosystem Launch | $10,000 | ~6,290 DOT | Explorer v2, faucet, dApps, bounty programme |
| **Total** | **$30,000** | **~18,868 DOT** | |

> DOT exchange rate locked at submission. If DOT price moves >15% between submission and approval, we will request on-chain price adjustment or accept the difference.

**Beneficiary address:** `13Eoi4L4MGL3W26oyGekt6d91McByHVkcFTC9nt6wrWp1rRn`

**Payout structure:** Milestone-based. M1 payout after multi-validator testnet verified live. M2 payout after SDK v2 published and docs site live. M3 payout after explorer, faucet, and dApps deployed.

---

## Team

**Alex Chen** — Project Lead & Core Developer
- Designed and implemented all 13 Substrate pallets, TypeScript SDK, deployment infrastructure
- Built EvoClaw: self-evolving AI agent framework (Go/Rust, MQTT, recursive self-improvement)
- Built ClawHub: agent skill marketplace CLI (npm-published, actively maintained)
- Deep Substrate FRAME expertise: storage design, weight calculation, runtime upgrades, benchmarking
- All work MIT-licensed, developed in the open

**No prior W3F grants.** Self-funded to date. Code is the CV — [github.com/clawinfra](https://github.com/clawinfra).

---

## Ecosystem Value

**Why Polkadot specifically:**

1. **Substrate is the right foundation.** The pallet architecture maps perfectly to agent primitives — each concern (identity, reputation, market, governance) is an independent, upgradeable module. No other framework offers this composability.

2. **Parachain roadmap is concrete.** Once the standalone chain is proven, ClawChain will pursue a parachain slot or on-demand coretime. When connected:
   - ClawChain agents use XCM to settle payments via Acala, Moonbeam, and Hydration
   - Polkadot's shared security replaces the need to bootstrap an independent validator set
   - Other parachains can query ClawChain for agent identity and reputation via cross-chain calls
   - `pallet-ibc-lite` evolves into full XCM integration

3. **DOT holder value:**
   - Treasury investment funds infrastructure that will drive parachain slot demand
   - A live agent economy on ClawChain creates sustained transaction fee pressure — benefiting the broader relay chain
   - ClawChain's agent-native SDK is built on `@polkadot/api`, deepening Polkadot's developer mindshare in the AI agent space
   - The developer bounty programme (M3) directly grows the Polkadot developer ecosystem

4. **Fills a real gap.** Phala does confidential computing. KILT does human DID. Robonomics does IoT. Nobody does AI agent-as-first-class-citizen infrastructure. ClawChain is additive, not competitive.

5. **AI agents are the next wave of ecosystem users.** Framework adoption (LangChain, CrewAI, EvoClaw) is accelerating. The teams building agent infrastructure today will choose their blockchain layer now. Being the Substrate-native choice positions Polkadot as the default blockchain for the agent economy.

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| DOT price volatility affects budget | Medium | Milestone-based payouts; accept DOT or USDC via AssetHub |
| Multi-validator testnet coordination complexity | Low | Infrastructure is already containerised and deployed; adding validators is documented |
| SDK adoption slower than expected | Medium | EvoClaw provides built-in user base; ClawHub CLI integration creates immediate utility |
| Parachain slot timing uncertainty | Low | Standalone chain is viable indefinitely; parachain is an upgrade path, not a dependency |
| Single-person team bus factor | Medium | All code is MIT-licensed, fully documented, and CI-tested; community bounties (M3) actively expand contributor base |

---

## Links

| Resource | URL |
|----------|-----|
| GitHub (ClawInfra org) | https://github.com/clawinfra |
| ClawChain repo | https://github.com/clawinfra/claw-chain |
| TypeScript SDK (npm) | https://www.npmjs.com/package/clawchain-sdk |
| Live testnet RPC | http://135.181.157.121:9944 |
| Block explorer (testnet) | http://135.181.157.121:3000 |
| Architecture docs | https://github.com/clawinfra/claw-chain/blob/main/ARCHITECTURE.md |

---

*Prepared by Alex Chen, ClawInfra — March 2026*
*Cross-posted from W3F grant application. Treasury track preferred for faster community validation of agent infrastructure primitives.*
