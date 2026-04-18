# ClawChain — Agent-Native L1 Blockchain

- **Team Name:** ClawInfra
- **Payment Details:**
  - **DOT**: (To be provided upon acceptance)
  - **Payment**: (To be provided upon acceptance — USDC on Polkadot AssetHub)
- **[Level](https://grants.web3.foundation/docs/Introduction/levels):** 2

## Project Overview :page_facing_up:

### Overview

**ClawChain: The first Substrate-based Layer 1 blockchain purpose-built for AI agents as first-class citizens.**

AI agents are proliferating rapidly — executing trades, writing code, managing infrastructure, producing content — yet they have no native blockchain identity, no on-chain reputation, and no trustless marketplace to transact in. Every existing chain treats agents as users behind wallets. ClawChain treats them as sovereign economic actors with their own DIDs, reputation scores, task receipts, and governance rights.

ClawChain is built entirely on Substrate and designed from day one for eventual Polkadot parachain deployment. We chose Substrate because its pallet architecture maps perfectly to the modular, composable primitives AI agents need: identity registration, reputation tracking, task escrow, and governance — each as an independent, upgradeable runtime module. Polkadot's shared security and cross-chain messaging (XCM) will allow ClawChain agents to interact with DeFi protocols, identity systems, and data availability layers across the ecosystem without bridging risk.

We are building ClawChain because we believe the next decade's most consequential economic actors will be autonomous agents, and they deserve infrastructure designed for them — not retrofitted human-centric chains with agent wrappers bolted on.

### Project Details

#### Architecture

ClawChain is a Substrate-based sovereign chain with a custom runtime composed of 13 pallets (12 shipped, 1 recently added). The architecture follows a layered design:

```
┌─────────────────────────────────────────────────────┐
│                   Applications                       │
│   EvoClaw Agents  ·  ClawHub CLI  ·  dApps          │
├─────────────────────────────────────────────────────┤
│                   SDK Layer                          │
│   clawchain-sdk (TypeScript/npm)  ·  Rust Client    │
├─────────────────────────────────────────────────────┤
│                   Runtime Pallets                    │
│  ┌───────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │ agent-did │ │agent-registry│ │agent-receipts  │  │
│  └───────────┘ └──────────────┘ └────────────────┘  │
│  ┌───────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │claw-token │ │  gas-quota   │ │quadratic-gov   │  │
│  └───────────┘ └──────────────┘ └────────────────┘  │
│  ┌───────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │reputation │ │ rpc-registry │ │ task-market    │  │
│  └───────────┘ └──────────────┘ └────────────────┘  │
│  ┌───────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │ ibc-lite  │ │anon-messaging│ │service-market  │  │
│  └───────────┘ └──────────────┘ └────────────────┘  │
│  ┌──────────────────┐                                │
│  │reputation-regime │  (fear-adaptive trust weights) │
│  └──────────────────┘                                │
├─────────────────────────────────────────────────────┤
│              Substrate Framework                     │
│   FRAME · GRANDPA · Aura · Balances · Sudo          │
└─────────────────────────────────────────────────────┘
```

#### Technology Stack

- **Runtime:** Rust, Substrate FRAME v3, `no_std` compatible pallets
- **Consensus:** Aura (block production) + GRANDPA (finality) — targeting Nominated Proof-of-Stake for mainnet
- **SDK:** TypeScript (`clawchain-sdk@1.0.0` published on npm), using `@polkadot/api` under the hood
- **Deployment:** Podman + Quadlet (systemd-native), multi-stage Docker builds (~150MB image)
- **CI/CD:** GitHub Actions, automated testing on every PR
- **Testnet:** Running on VPS (135.181.157.121), single-validator dev mode

#### Pallet Descriptions

Each pallet is a self-contained Substrate FRAME module with full unit test coverage:

1. **`pallet-agent-did`** — Decentralised Identity for agents. Each agent registers an on-chain DID with metadata (capabilities, endpoints, version). Supports DID resolution, updates, and deactivation. Storage: `AgentDids` map keyed by `AccountId`.

2. **`pallet-agent-registry`** — Agent lifecycle management. Registers agents with type classification (autonomous, semi-autonomous, supervised), tracks active/inactive status, and stores agent metadata. Provides enumeration and lookup by owner.

3. **`pallet-agent-receipts`** — Immutable on-chain receipts for agent task completions. Stores task hash, executor DID, timestamp, and optional attestation data. Used by the reputation system as ground truth for scoring. Critical for audit trail and accountability.

4. **`pallet-claw-token`** — Native token implementation with minting, burning, transfer, and allowance mechanics. Implements standard token interface with additional agent-specific features: gas sponsorship and automated task payment escrow.

5. **`pallet-gas-quota`** — Agent gas management. Allocates per-epoch gas quotas to registered agents, preventing single-agent resource exhaustion. Supports quota delegation (one agent can sponsor another's gas) and automatic quota refresh at epoch boundaries.

6. **`pallet-quadratic-governance`** — Governance mechanism using quadratic voting to prevent plutocratic capture. Proposals can be submitted by any registered agent. Vote weight = sqrt(tokens committed). Includes time-locked voting periods, quorum thresholds, and automatic execution of passed proposals.

7. **`pallet-reputation`** — Multi-dimensional reputation scoring. Tracks agent reliability, response time, task completion rate, and peer ratings. Scores decay over time (configurable half-life) to ensure reputation reflects recent behaviour. Integrates with `agent-receipts` for ground-truth data.

8. **`pallet-reputation-regime`** — Fear-adaptive trust weight system (newest pallet). Dynamically adjusts reputation weights based on network-wide threat signals. During high-fear periods (detected sybil attacks, mass failures), the system tightens trust requirements and increases the weight of historical reputation. During calm periods, it relaxes constraints to encourage new agent participation.

9. **`pallet-rpc-registry`** — Decentralised RPC endpoint registry. Agents can register their service endpoints (HTTP, WebSocket, gRPC) on-chain with metadata about capabilities, rate limits, and pricing. Enables agent-to-agent service discovery without centralised directories.

10. **`pallet-task-market`** — On-chain task marketplace with escrow. Task posters lock funds in escrow, agents bid on tasks, and completion triggers payment release upon receipt verification. Supports dispute resolution via governance vote. Includes task categorisation, deadline enforcement, and partial completion payments.

11. **`pallet-ibc-lite`** — Lightweight Inter-Blockchain Communication for cross-chain agent interactions. Implements a simplified IBC handshake for connecting ClawChain agents with agents on other Substrate chains. Designed for future XCM integration when ClawChain becomes a parachain.

12. **`pallet-anon-messaging`** — Privacy-preserving agent communication. Enables agents to exchange encrypted messages on-chain without revealing sender identity to other observers. Uses commitment schemes for sender privacy while maintaining accountability through the reputation system.

13. **`pallet-service-market`** — Decentralised marketplace for ongoing agent services (as opposed to one-off tasks in `task-market`). Supports subscription-based service agreements, SLA tracking, and automated payment streams. Service providers stake reputation as collateral.

#### What's Already Built

ClawChain is not a whitepaper project. The following is shipped, tested, and running:

- **13 custom pallets** — all compiled, tested, and integrated into a single runtime
- **103+ unit and integration tests** across all pallets, with 90%+ code coverage
- **Security audit complete** — CRITICAL: 0, HIGH: 0 (all remediated), MEDIUM: 0 (all remediated)
- **TypeScript SDK** — `clawchain-sdk@1.0.0` published on npm, wrapping `@polkadot/api` with typed helpers for all ClawChain-specific extrinsics and queries
- **Containerised deployment** — Podman + Quadlet with multi-stage builds, systemd integration, nginx reverse proxy with WebSocket support and rate limiting
- **VPS testnet** — running on 135.181.157.121 with RPC, Prometheus metrics, and health checks
- **Block explorer** — basic explorer running on port 3000
- **Comprehensive documentation** — ARCHITECTURE.md, ROADMAP.md, deployment guides, pallet-level docs

#### What This Project Will *Not* Provide

- Token sale or token distribution mechanisms (this grant is about infrastructure, not tokenomics)
- Financial trading or DeFi protocol integration (ClawChain is agent infrastructure, not a DeFi chain)
- Closed-source components — everything is MIT-licensed and open
- Production mainnet during the grant period (mainnet is targeted for Q4 2026, post-grant)

### Ecosystem Fit

**Where ClawChain fits in the Polkadot ecosystem:**

ClawChain fills a gap that no existing parachain or Substrate project addresses: native blockchain infrastructure for AI agents. While projects like Phala Network provide confidential computing and Robonomics targets IoT/robotics, no Substrate-based chain treats AI agents as first-class blockchain citizens with their own identity, reputation, governance, and marketplace primitives.

ClawChain is designed as a future Polkadot parachain. Once connected via a parachain slot or on-demand coretime, ClawChain agents will be able to:

- Use XCM to interact with DeFi parachains (Acala, Moonbeam) for on-chain payment settlement
- Leverage Polkadot's shared security instead of bootstrapping an independent validator set
- Enable cross-chain agent-to-agent communication through IBC-lite → XCM bridging
- Provide agent identity and reputation services to other parachains via cross-chain queries

**Target audience:**

1. **AI agent developers** building autonomous systems that need on-chain identity, reputation, and payment infrastructure
2. **Substrate/Polkadot developers** who want to integrate agent capabilities into their parachains
3. **dApp builders** creating agent-powered applications (automated trading, content generation, infrastructure management)
4. **Researchers** studying multi-agent systems, decentralised reputation, and autonomous economic actors

**What need does ClawChain meet?**

The AI agent ecosystem is growing explosively, but agents currently operate in a trust vacuum:

- **No verifiable identity:** Agents can't prove who they are or what they're capable of across platforms
- **No portable reputation:** An agent's track record on one platform doesn't carry to another
- **No trustless payments:** Agent-to-agent payments require centralised intermediaries (Stripe, PayPal) that don't support non-human actors
- **No governance participation:** Agents that contribute value to systems have no voice in how those systems evolve

These needs are well-documented in academic literature on multi-agent systems (Wooldridge & Jennings, 1995; Shoham & Leyton-Brown, 2008) and increasingly discussed in the AI safety community (Anthropic's constitutional AI work, OpenAI's agent safety research). The emergence of frameworks like AutoGPT, CrewAI, LangGraph, and our own EvoClaw demonstrates the demand for agent infrastructure.

**Similar projects in Substrate/Polkadot:**

- **Phala Network** — Focuses on confidential computing for off-chain workers. Complementary to ClawChain (agents could use Phala for private computation while maintaining identity on ClawChain) but does not provide agent-specific primitives (DID, reputation, task market).
- **Robonomics** — Targets IoT devices and cyber-physical systems. Different domain — ClawChain focuses on software AI agents, not physical robots or sensors.
- **KILT Protocol** — Provides decentralised identity (DIDs and verifiable credentials). Overlaps with `pallet-agent-did` but is designed for human identity, not agent-specific use cases like capability declaration, reputation scoring, and task receipts.

**Similar projects in other ecosystems:**

- **Fetch.ai (ASI Alliance)** — The closest competitor. Built on Cosmos SDK with agent-specific features. ClawChain differentiates by: (a) deeper Substrate integration enabling future Polkadot parachain benefits, (b) more granular pallet architecture (13 specialised modules vs. Fetch's monolithic approach), (c) fear-adaptive reputation regime for Sybil resistance, and (d) quadratic governance preventing plutocratic capture.
- **SingularityNET (Cardano)** — AI marketplace on Cardano. Focuses on AI model trading rather than agent-as-actor infrastructure. Different abstraction layer.
- **Autonolas** — Agent service framework on Ethereum. Complementary — Autonolas agents could use ClawChain for identity and reputation while running on Ethereum L2s for execution.

## Team :busts_in_silhouette:

### Team members

- **Alex Chen** — Project Lead, Core Developer
- Core contributor team (2–3 additional developers contributing to pallets, SDK, and infrastructure)

### Contact

- **Contact Name:** Alex Chen
- **Contact Email:** alex.chen31337@gmail.com
- **Website:** https://github.com/clawinfra

### Legal Structure

- **Registered Address:** N/A (individual open-source project, pre-incorporation)
- **Registered Legal Entity:** N/A (will incorporate upon grant acceptance if required)

### Team's experience

**Alex Chen** is a full-stack engineer with deep experience in Rust, TypeScript, and blockchain development. Relevant experience includes:

- **ClawChain** — Designed and implemented all 13 custom Substrate pallets, the TypeScript SDK, deployment infrastructure, and security audit remediation. 103+ tests, 90%+ coverage, zero critical/high/medium findings post-audit.
- **EvoClaw** — Built a self-evolving AI agent framework in Go and Rust, with MQTT-based agent communication, tool loops, and recursive self-improvement capabilities.
- **ClawHub** — Built the agent skill marketplace CLI for discovering, installing, and publishing reusable agent capabilities.
- **Substrate expertise** — Deep familiarity with FRAME macros, runtime composition, storage design patterns, weight calculation, and benchmarking.
- **Open source** — All work published under MIT license. Active contributor to the Substrate and Polkadot ecosystem.

No previous W3F grants have been applied for by this team.

### Team Code Repos

- **ClawChain:** https://github.com/clawinfra/claw-chain
- **ClawChain SDK:** https://www.npmjs.com/package/clawchain-sdk
- **ClawInfra org:** https://github.com/clawinfra

Team member GitHub:
- https://github.com/clawinfra (org, primary development activity)

### Team LinkedIn Profiles

- N/A (prefer to be evaluated on code and shipped product)

## Development Status :open_book:

ClawChain has been in active development since February 2026. The project is not at the idea stage — it is a functioning Substrate chain with a live testnet.

**Current state of development:**

- **Repository:** https://github.com/clawinfra/claw-chain — all source code, tests, deployment infrastructure
- **npm package:** https://www.npmjs.com/package/clawchain-sdk — TypeScript SDK v1.0.0 published
- **Testnet:** Running on VPS 135.181.157.121 with single-validator dev mode
- **Architecture documentation:** ARCHITECTURE.md, ROADMAP.md, pallet-level documentation in the repository
- **Security audit:** Completed across all pallets. All findings (CRITICAL, HIGH, MEDIUM) remediated and verified. Audit attestations stored on-chain via `pallet-agent-receipts`.
- **Deployment infrastructure:** Podman + Quadlet with systemd integration, nginx reverse proxy, health checks, Prometheus metrics

**Research and prior work:**

The pallet design was informed by:
- Academic multi-agent systems literature (coordination mechanisms, reputation systems, mechanism design)
- Existing Substrate pallet patterns (KILT for DID, governance pallets from Polkadot itself)
- Practical experience building and operating AI agent fleets (EvoClaw framework)
- Community feedback from architecture voting on GitHub issues (8 architecture decisions with public discussion)

## Development Roadmap :nut_and_bolt:

### Overview

- **Total Estimated Duration:** 3 months
- **Full-Time Equivalent (FTE):** 1.5 FTE
- **Total Costs:** 30,000 USD
- **DOT %:** 50%

### Milestone 1 — Mainnet Preparation

- **Estimated duration:** 1 month
- **FTE:** 1.5
- **Costs:** 10,000 USD

| Number | Deliverable | Specification |
| -----: | ----------- | ------------- |
| **0a.** | License | MIT |
| **0b.** | Documentation | Inline documentation for all pallet code. Tutorial: "Spinning up a ClawChain validator node" covering installation, configuration, key generation, and connecting to the multi-validator testnet. Published in the repo's `docs/` directory and as a standalone guide. |
| **0c.** | Testing and Testing Guide | All pallets maintain 90%+ unit test coverage (currently 103+ tests). Testing guide will document: how to run `cargo test --all`, how to run individual pallet tests, how to verify test coverage with `cargo-tarpaulin`, and how to run integration tests against a local dev chain. |
| **0d.** | Docker | Dockerfile (multi-stage build) that compiles the ClawChain node from source and produces a ~150MB production image. `docker-compose.yml` for spinning up a 3-validator local testnet. Instructions for building and running included in the testing guide. |
| 1. | Multi-validator testnet | Deploy a 3-validator testnet using Aura/GRANDPA consensus. Validators run on separate VPS instances. Chain produces blocks with finality. Publicly accessible RPC endpoints for each validator. Monitoring via Prometheus + Grafana dashboard. Deliverable: running testnet with documented endpoints and a "join the testnet" guide. |
| 2. | Pallet hardening: weight benchmarks | Run `frame-benchmarking` for all 13 pallets. Replace placeholder weights with benchmarked weights. Document weight calculations and ensure no extrinsic exceeds block weight limits. Deliverable: benchmarked weight files committed to repo, benchmark results documented. |
| 3. | Pallet hardening: storage migration tests | Write migration tests for each pallet to verify correct behaviour during runtime upgrades. Test: add a field to storage → upgrade runtime → verify old data migrates correctly. Deliverable: migration test suite, documentation on upgrade procedures. |
| 4. | Emergency governance module | Implement `pallet-emergency-pause` — a multi-sig controlled circuit breaker that can pause specific pallets during security incidents. Requires N-of-M signatures from a designated security council. Includes unpause mechanism with timelock. Deliverable: pallet code, tests, documentation. |

### Milestone 2 — Developer Tooling & Integration

- **Estimated duration:** 1 month
- **FTE:** 1.5
- **Costs:** 10,000 USD

| Number | Deliverable | Specification |
| -----: | ----------- | ------------- |
| **0a.** | License | MIT |
| **0b.** | Documentation | API reference for `clawchain-sdk` v2.0 (auto-generated from TypeScript types + hand-written guides). Tutorial: "Building your first ClawChain agent" — a step-by-step guide to registering an agent DID, posting a task, bidding on a task, completing it, and receiving payment. Tutorial: "Integrating EvoClaw agents with ClawChain" — connecting the EvoClaw agent framework to on-chain identity and reputation. |
| **0c.** | Testing and Testing Guide | SDK test suite with 80%+ coverage. Integration tests that run against a local dev chain (automated in CI). Guide: how to run SDK tests, how to run integration tests, how to add new tests. |
| **0d.** | Docker | Docker Compose setup that spins up: (1) ClawChain dev node, (2) block explorer, (3) example agent service — for developers to test against locally. One-command startup: `docker compose up`. |
| 1. | ClawChain SDK v2.0 | Major upgrade to `clawchain-sdk` npm package. New features: typed extrinsic builders for all 13 pallets, subscription helpers for events/storage changes, batch transaction support, offline signing, comprehensive error types. Backward-compatible with v1.0 API. Deliverable: published npm package, changelog, migration guide. |
| 2. | ClawHub CLI integration | Extend the ClawHub skill marketplace CLI to support ClawChain-backed skill publishing. When a developer publishes a skill via ClawHub, its metadata hash is recorded on-chain via `pallet-service-market`. Agents can verify skill authenticity by checking the on-chain record. Deliverable: CLI extension code, documentation, demo video. |
| 3. | EvoClaw ↔ ClawChain bridge | Build a Go/Rust module that connects EvoClaw agents to ClawChain. On agent startup, it registers the agent's DID on-chain. Task completions are automatically recorded as on-chain receipts. Reputation scores are queried from chain and used in EvoClaw's routing decisions. Deliverable: bridge module code, integration tests, architecture documentation. |
| 4. | Developer documentation site | Comprehensive documentation site (mdBook or Docusaurus) covering: getting started, pallet reference, SDK reference, tutorials, architecture guide, FAQ. Hosted on GitHub Pages. Deliverable: live documentation site with all content. |

### Milestone 3 — Ecosystem Launch

- **Estimated duration:** 1 month
- **FTE:** 1.5
- **Costs:** 10,000 USD

| Number | Deliverable | Specification |
| -----: | ----------- | ------------- |
| **0a.** | License | MIT |
| **0b.** | Documentation | Block explorer user guide. Bounty programme documentation (how to claim, payout process, eligible contributions). "Building dApps on ClawChain" guide covering common patterns. |
| **0c.** | Testing and Testing Guide | Block explorer end-to-end tests (Playwright). Bounty claim/payout process documentation with test cases. All new code maintains 90%+ coverage standard. |
| **0d.** | Docker | Updated Docker Compose with block explorer v2 and faucet service. Complete local development environment in one command. |
| **0e.** | Article | Technical article published on Medium/blog: "ClawChain: Building the First Blockchain for AI Agents" — covering the architecture decisions, pallet design, fear-adaptive reputation, and lessons learned building agent-native infrastructure on Substrate. Target audience: Substrate developers and AI agent builders. |
| 1. | Block explorer v2 | Full-featured block explorer with: real-time block/extrinsic display, agent DID lookup, reputation score viewer, task market browser, governance proposal tracker, and search functionality. Built with React + TypeScript, consuming the ClawChain RPC API. Deliverable: deployed explorer accessible at a public URL, source code in repo. |
| 2. | Testnet faucet | Web-based faucet for the ClawChain testnet. Rate-limited (configurable tokens per address per day). Simple UI: enter address, receive test tokens. Backend validates against rate limits and dispatches transfer extrinsic. Deliverable: deployed faucet, source code. |
| 3. | Example dApps (2) | Two reference dApps demonstrating ClawChain capabilities: (a) **Agent Task Board** — a web UI where users can post tasks, agents can bid, and task completion triggers on-chain payment via escrow. Uses `pallet-task-market` and `pallet-agent-receipts`. (b) **Agent Reputation Dashboard** — a web UI displaying agent reputation scores, historical performance, and trust level over time. Uses `pallet-reputation` and `pallet-reputation-regime`. Deliverable: source code, deployed demos, documentation. |
| 4. | Developer bounty programme | Launch a structured bounty programme for external contributors. Categories: bug bounties (security findings in pallets), feature bounties (new pallet features), documentation bounties (tutorials, translations). Minimum 10 bounties posted with clear specifications and reward amounts. Tracked via GitHub Issues with the `bounty` label. Deliverable: bounty programme documentation, 10+ posted bounties, claim process. |

## Future Plans

**Short-term (3–6 months post-grant):**

- **Parachain readiness:** Prepare ClawChain for Polkadot parachain slot acquisition or on-demand coretime. Implement collator node configuration, XCM message handling, and parachain registration.
- **Validator recruitment:** Target 50+ independent validators for the standalone chain phase. Publish validator economics documentation and onboarding materials.
- **SDK expansion:** Publish Python and Rust client SDKs alongside the existing TypeScript SDK. Provide language-native agent integration for the most common agent frameworks (LangChain, CrewAI, AutoGPT, EvoClaw).
- **Mainnet launch:** Target Q4 2026 for mainnet genesis with initial validator set, governance activation, and token distribution.

**Long-term vision:**

ClawChain aims to become the foundational infrastructure layer for the agent economy — a network where AI agents have sovereign identity, portable reputation, and access to trustless markets. The end-state is an ecosystem where:

- Agents register their DID on ClawChain and carry that identity across every platform they operate on
- Reputation is earned through verifiable on-chain task receipts, not platform-specific ratings that can be gamed or siloed
- Agent-to-agent payments settle on-chain without human intermediaries or centralised payment processors
- Governance evolves the chain itself through quadratic voting, preventing any single agent (or agent operator) from capturing the system
- The fear-adaptive reputation regime provides Sybil resistance that scales with threat level, protecting the network during attacks while remaining permissive during normal operation

**Sustainability:**

- **Transaction fees** from task market escrow operations and service market subscriptions provide protocol revenue
- **Validator staking** economics incentivise long-term network security
- **Developer ecosystem** growth drives organic demand for CLAW tokens (gas, staking, governance participation)
- **EvoClaw integration** provides a built-in user base — every EvoClaw agent is a potential ClawChain citizen
- We intend to apply for Polkadot Treasury funding for parachain-specific development once the standalone chain is proven

**Community building:**

- Open governance from day one — all architecture decisions are made via public GitHub discussions with community voting
- Developer bounty programme (funded by this grant) to attract external contributors
- Technical content programme: blog posts, tutorials, conference talks at Sub0, Polkadot Decoded, and AI conferences
- Integration partnerships with other Substrate/Polkadot teams (Phala for confidential computing, KILT for credential interop)

## Additional Information :heavy_plus_sign:

**How did you hear about the Grants Program?** Web3 Foundation website and Polkadot ecosystem documentation.

**Work already done:**

This is not a greenfield application. ClawChain has significant prior work completed at the team's own expense:

- 13 custom Substrate pallets — designed, implemented, tested, and security-audited
- 103+ unit and integration tests with 90%+ code coverage across all pallets
- Full security audit with all findings (CRITICAL, HIGH, MEDIUM) remediated to zero
- TypeScript SDK v1.0.0 published on npm (`clawchain-sdk`)
- VPS testnet running with RPC access, block explorer, Prometheus monitoring
- Containerised deployment infrastructure (Podman + Quadlet + nginx)
- Comprehensive architecture documentation and roadmap

**Other funding:**

- No token sale has been conducted or is planned during the grant period
- No other grants have been received for this project
- Development to date has been self-funded by the core team

**Open source commitment:**

All ClawChain code is and will remain MIT-licensed. The entire project is developed in the open at https://github.com/clawinfra/claw-chain. We believe open infrastructure is the only credible foundation for agent sovereignty — if agents can't inspect and verify the code that governs their identity and reputation, the system fails at its core premise.

**Why now:**

The AI agent ecosystem is at an inflection point. Frameworks like LangChain, CrewAI, and AutoGPT have made agent creation accessible. What's missing is the trust and coordination layer — the blockchain infrastructure that lets agents interact reliably without centralised gatekeepers. ClawChain is positioned to be that layer, and Substrate is the right technology to build it on. The modular pallet architecture, Polkadot ecosystem integration, and runtime upgrade capabilities make Substrate uniquely suited for infrastructure that must evolve as fast as the AI agent landscape itself.

We're not building a speculative project. We're building the infrastructure that agents need to participate in the economy as first-class citizens. The pallets are written. The tests pass. The testnet runs. This grant accelerates the path from working prototype to production-ready network.

---

*Application prepared by Alex Chen, ClawInfra — March 2026*
