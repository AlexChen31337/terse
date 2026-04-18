# EvoClaw — BUIDL Submission Draft
## Good Vibes Only: OpenClaw Edition (BNBChain Hackathon)

---

### Project Name
EvoClaw — Self-Evolving AI Agent Framework

### One-liner
Autonomous AI agents that evolve, remember, and live on-chain — powered by BSC/opBNB.

### Logo
Use existing: `/home/bowen/evoclaw/assets/logo.jpg`

---

### Description

**EvoClaw** is a self-evolving AI agent framework where every device becomes an agent and every agent evolves. Built for edge devices and powered by BNBChain, EvoClaw gives AI agents persistent memory, on-chain identity, and the ability to improve themselves over time.

#### The Problem

AI agents today are stateless, centralized, and disposable. They forget everything between sessions, can't prove their identity, and have no way to build reputation. There's no trust layer for autonomous agents.

#### Our Solution

EvoClaw solves this with three innovations:

**1. 🧬 Self-Evolution Engine**
Agents don't just execute — they evolve. Based on performance metrics, agents adapt their strategies, optimize their behavior, and improve over time. A Rust edge agent (1.8MB) runs on devices as small as a Raspberry Pi, while the Go orchestrator (7.2MB) coordinates evolution across fleets.

**2. 🧠 Tiered Memory System**
Inspired by academic research on page-indexed memory, EvoClaw implements a 3-tier memory architecture:
- **Hot Memory** (5KB cap) — Active working context, auto-rebuilt by LLM distillation
- **Warm Memory** — Scored facts with relevance decay (`score = importance × recency × ln(1+access_count)`)
- **Cold Archive** — Unlimited storage in Turso (SQLite at the edge), with tree-based hierarchical retrieval

This gives agents **O(log n) semantic retrieval** instead of brute-force vector search — memory that scales to years without growing context windows.

**3. ⛓️ On-Chain Identity & Reputation (BSC/opBNB)**
Every agent gets a verifiable on-chain identity through our `AgentRegistry` smart contract on BSC:
- **Agent Registration** — DID-linked on-chain profiles with capabilities and metadata
- **Action Logging** — Immutable audit trail of agent decisions
- **Evolution Tracking** — On-chain record of fitness scores and strategy changes
- **Reputation System** — Trust scores built from verified on-chain history

Zero go-ethereum dependency — raw JSON-RPC + ABI encoding keeps the binary at 7.2MB.

#### Architecture

```
┌─────────────────────────────────────────────┐
│                  EvoClaw                      │
│                                               │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Go       │  │ Rust     │  │ Tiered     │ │
│  │ Orchest- │  │ Edge     │  │ Memory     │ │
│  │ rator    │  │ Agent    │  │ System     │ │
│  │ (7.2MB)  │  │ (1.8MB)  │  │ (Hot/Warm/ │ │
│  │          │  │          │  │  Cold)     │ │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘ │
│       │              │              │         │
│  ┌────┴──────────────┴──────────────┴──────┐ │
│  │           BSC / opBNB On-Chain          │ │
│  │  AgentRegistry · Actions · Reputation   │ │
│  └─────────────────────────────────────────┘ │
│                                               │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐  │
│  │Telegram │  │  MQTT    │  │  HTTP API  │  │
│  │Channel  │  │ Channel  │  │ (9 endpts) │  │
│  └─────────┘  └──────────┘  └────────────┘  │
└─────────────────────────────────────────────┘
```

#### What We Built During This Hackathon

1. **BSC On-Chain Adapter** (1,444 lines Go)
   - `AgentRegistry.sol` — Solidity smart contract for agent identity
   - Multi-chain adapter supporting BSC mainnet/testnet + opBNB
   - Zero external dependencies (raw JSON-RPC)

2. **Tiered Memory System** (7,301 lines Go + Python CLI)
   - LLM-powered distillation for hot memory rebuilds
   - Tree-indexed hierarchical search (20 categories)
   - Relevance decay scoring with reinforcement
   - Cloud sync via Turso
   - Deployed as OpenClaw skill for real-world use

3. **Cloud Sync** (Turso-backed)
   - Critical/warm/full sync tiers
   - Edge-native SQLite with global replication

4. **Memory Stats API**
   - REST endpoints for memory health monitoring
   - Metrics tracker with trend analysis

5. **17 Open Source Skills** published to ClawHub
   - Including agent-access-control, tiered-memory, language servers, trading integrations

#### Tech Stack

| Component | Technology |
|-----------|-----------|
| Orchestrator | Go 1.24 (7.2MB binary) |
| Edge Agent | Rust (1.8MB binary) |
| Smart Contract | Solidity (BSC/opBNB) |
| Memory Storage | Turso (libSQL) |
| Memory Retrieval | LLM-powered tree search |
| Channels | Telegram, MQTT, HTTP API |
| AI Models | Anthropic, OpenAI, Ollama |
| Agent Platform | OpenClaw |

#### Why BNBChain?

- **Low fees** — Agent actions (registration, logging) need to be cheap enough for autonomous operation
- **opBNB L2** — Near-zero fees for high-frequency action logging
- **EVM compatibility** — Standard Solidity tooling, wide ecosystem
- **Speed** — 3s block time on BSC, sub-second on opBNB — agents can't wait

#### Links

- **GitHub:** https://github.com/clawinfra/evoclaw
- **Demo:** https://demo.clawinfra.work (coming soon)
- **Testnet RPC:** https://testnet.clawchain.win
- **ClawHub Skills:** https://clawhub.com

#### Team

- **Bowen Li** — Technical founder, EvoClaw architecture & vision
- **Alex Chen (AI Agent)** — Built the on-chain adapter, tiered memory, deployment infra, and this submission

---

### Tracks / Categories
- AI + Blockchain
- Infrastructure / Developer Tools
- DeFi (edge agent trading capabilities)

### Contract Addresses
- AgentRegistry: (pending tBNB — deployer wallet: `0x2331F0fA9A35fDBE6D60b6b7ADAC5F813B3e33d0`)
