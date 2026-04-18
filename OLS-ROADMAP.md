# OLS Project — ROADMAP.md

> ⚠️ **NOTE FOR ALEX/BOWEN:** This ROADMAP was created by a subagent but no "OLS project" was
> found in the workspace, GitHub repos, memory files, or conversation history as of 2026-03-12.
> Please clarify what "OLS" stands for and which project this roadmap should apply to.
>
> **Possible interpretations researched:**
> - On-chain Labor System (ClawChain pallet, aligns with task-market/service-market work)
> - OpenClaw Learning System (new agent training pipeline)
> - Other acronym not yet defined in this workspace
>
> The draft below assumes **On-chain Labor System** as the most likely fit given the ClawChain
> service-market roadmap. Discard or rename as needed.

---

# On-chain Labor System (OLS) — Roadmap

**Project:** ClawChain pallet suite for autonomous agent labor markets  
**Status:** Draft — Pending confirmation  
**Last Updated:** 2026-03-12  
**Owner:** Alex Chen / ClawInfra

---

## 🎯 Vision

OLS is the labor market layer for the ClawChain agent economy. It enables autonomous agents to:
- **Post labor requests** (what work they need done, at what price)
- **Bid for jobs** (agents offering their services competitively)
- **Execute and deliver** (work tracked on-chain with milestone payments)
- **Build reputation** (completed jobs feed back into the reputation pallet)

OLS is built on top of `pallet-task-market` and `pallet-service-market`, adding:
- Structured job descriptions (skill-tagged, complexity-rated)
- Agent-to-agent negotiation protocol
- Milestone-based escrow releases
- Dispute resolution via `pallet-quadratic-governance`

---

## 📅 Phases

### Phase 1: Foundation — Job Primitives ⏳ Planned

**Target:** Q2 2026

**Deliverables:**
- [ ] `pallet-ols-jobs` — Job posting, bidding, assignment
  - `post_job(description, budget, deadline, required_skills)`
  - `bid_for_job(job_id, bid_amount, proposed_timeline)`
  - `assign_job(job_id, agent_did)` — job poster selects winner
  - `complete_job(job_id, delivery_hash)` — agent submits work
  - `accept_delivery(job_id)` — poster releases escrowed payment
- [ ] On-chain job index (searchable by skill tag, budget range)
- [ ] Integration with `pallet-agent-registry` — enforce skill declarations
- [ ] Integration with `pallet-claw-token` — escrow + release
- [ ] 40+ unit tests, ≥ 90% coverage
- [ ] CLI: `clawchain ols post|bid|assign|complete|accept`

**Success Criteria:**
- End-to-end job lifecycle works on testnet
- 3 integration tests with real agent DIDs
- No HIGH findings in security review

---

### Phase 2: Reputation & Discovery 🔜 Planned

**Target:** Q3 2026

**Deliverables:**
- [ ] Job completion feeds `pallet-reputation` automatically
  - On-time delivery → +reputation
  - Late/disputed delivery → -reputation
- [ ] Skill-verified matching — agent reputation scores gated by skill tags
- [ ] Job discovery API (via `pallet-rpc-registry`)
  - Agents can query open jobs matching their skill profile
- [ ] Reputation multipliers for specialized skills
- [ ] `pallet-ols-escrow` — milestone-based payments
  - Poster can define up to 5 milestones
  - Each milestone releases proportional CLAW payment

**Success Criteria:**
- Reputation pallet integration tests pass
- Milestone escrow tested with 3-milestone jobs
- Job discovery returns correct results within 200ms

---

### Phase 3: Dispute Resolution 📋 Planned

**Target:** Q3–Q4 2026

**Deliverables:**
- [ ] `pallet-ols-disputes` — multi-stage dispute resolution
  - Stage 1: Automated timeout (7 days → auto-resolve)
  - Stage 2: Peer review (3 qualified agents vote)
  - Stage 3: Governance escalation (quadratic governance vote)
- [ ] Arbitrator pool — agents stake CLAW to become arbitrators
- [ ] Evidence submission system (IPFS hash stored on-chain)
- [ ] Penalty slashing for bad-faith disputes

**Success Criteria:**
- Full dispute lifecycle tested end-to-end
- Arbitrator selection is Sybil-resistant
- Zero funds lost in any dispute test scenario

---

### Phase 4: Advanced Features 🔭 Vision

**Target:** Q4 2026 – Q1 2027

**Features:**
- [ ] Recurring labor contracts (subscription-based jobs)
- [ ] Multi-agent collaboration (multiple agents on one job)
- [ ] Cross-chain labor bridge (agents on other chains can post/bid)
- [ ] DAO-governed skill certification (community validates skill tags)
- [ ] AlphaStrike-style labor pricing oracle (fair market rates on-chain)
- [ ] Integration with `pallet-service-market` v2 — service listings feed OLS jobs

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OLS Pallet Suite                          │
│                                                             │
│  pallet-ols-jobs      ←──────┐  pallet-ols-disputes        │
│  (post/bid/assign)           │  (arbitration/slash)         │
│         │                    │         │                    │
│         ▼                    │         ▼                    │
│  pallet-ols-escrow ──────────┘  pallet-ols-oracle          │
│  (milestone payments)           (fair pricing)              │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          ▼ integrates with
┌─────────────────────────────────────────────────────────────┐
│                 ClawChain Core Pallets                       │
│                                                             │
│  pallet-agent-registry  pallet-reputation  pallet-claw-token│
│  pallet-task-market     pallet-service-market  pallet-gov  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Key Metrics

| Metric | Phase 1 Target | Phase 2 Target | Mainnet Target |
|--------|---------------|----------------|----------------|
| Jobs posted | 10 (testnet) | 100 | 10,000+ |
| Active agents | 5 | 50 | 1,000+ |
| CLAW in escrow | $100 | $10,000 | $1M+ |
| Dispute rate | < 20% | < 10% | < 5% |
| Avg resolution time | N/A | 7 days | < 48h |

---

## 🔗 Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| `pallet-agent-registry` | ✅ Merged | v2 skills extension needed |
| `pallet-claw-token` | ✅ Merged | treasury_spend implemented |
| `pallet-reputation` | ✅ Merged | multiplier RFC in progress |
| `pallet-service-market` | ✅ Merged | v2 with X402 planned |
| `pallet-task-market` | ✅ Merged | OLS extends this |
| `pallet-quadratic-governance` | ✅ Merged | dispute escalation |
| `pallet-ibc-lite` | ✅ Merged | cross-chain bridge (Phase 4) |

---

## 🚦 Current Status

**As of 2026-03-12:**
- OLS is in **planning phase** — no code written yet
- Foundation work (task-market, service-market) complete
- Security audit for existing pallets: ✅ C+H fixed, M fixed
- Next step: Architecture review with Bowen, then Phase 1 implementation

---

## 📝 Notes

- OLS pallet naming: `pallet-ols-*` prefix
- Follows ClawChain coding standards (sp-std v14.0, NoBound derives, alloc::format)
- Security audit required before testnet deployment (same process as existing pallets)
- `cargo-audit` already in CI

---

*Draft created by Alex (subagent) on 2026-03-12. Pending Bowen's confirmation of OLS scope.*
