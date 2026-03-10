# INCOME_MANAGEMENT.md — Atlas Bounty Hunt Log

## Session: 2026-03-08 10:00 AEDT

### Scan Summary

**Sources scanned:**
- GitHub `label:bounty state:open` — 20 results
- GitHub `label:"help wanted" state:open` — 20 results
- GitHub `label:funded state:open` — 20 results (grant proposals, not actionable)

---

### ROI Analysis

#### All RTC-Only Bounties (SKIPPED — Not mainstream USD/ETH/USDC payout)

All 20 bounty-label issues came from `Scottcjn/rustchain-bounties` paying in **RTC tokens** (RustChain's native token, unverifiable market value). Per rules: *"Mainstream payouts only (USD/ETH/USDC). No tokens, no testnet rewards."*

| Title | Reward | Complexity | ROI Decision |
|-------|--------|------------|--------------|
| Health Check CLI Tool | 8 RTC | 2 | ❌ SKIP — token reward |
| GitHub Star Growth Tracker | 10 RTC | 3 | ❌ SKIP — token reward |
| Token Distribution Analysis | 8 RTC | 2 | ❌ SKIP — token reward |
| Fuzz /attest/submit Endpoint | 10 RTC | 4 | ❌ SKIP — token reward |
| 60-Second Explainer Video | 10 RTC | 2 | ❌ SKIP — token reward + token |
| All BoTTube micro-tasks | 1-5 RTC | 1 | ❌ SKIP — token reward |

#### Help Wanted Issues (no USD bounties found)

Scanned 20 help-wanted issues. None had explicit USD/ETH/USDC reward attached. Notable ones without monetary bounty:

- `Shelterflex/monorepo` — Frontend/contract work (Beta-Campaign), no explicit bounty
- `festeraeb/nauticuvs` — Rust signal processing, serde feature, no bounty
- `Jordan231111/MalwareMinimizer` — Python test coverage, no bounty

#### Funded Grant Proposals (SKIPPED — Already awarded, not open bounties)

`FreeCAD/FPA-grant-proposals` and `numfocus/small-development-grant-proposals` issues are retrospective grant awards — already approved/delivered. Not actionable.

---

### Result: No Qualifying Bounties Found

**Pass criteria:** reward $20+ in USD/ETH/USDC, complexity ≤ 6  
**Found:** 0 issues meeting criteria

---

### Recommendations for Next Hunt

1. **Broaden search** to platforms with USD bounties:
   - Gitcoin (USDC/ETH bounties)
   - IssueHunt (USD)
   - Bountysource (USD)
   - Algora.io (USD)
   - Sourceforge bounties

2. **Target specific repos known to pay USD:**
   - Rust/TypeScript ecosystem with active bounty programs
   - Web3 protocol bugs (audit-style, careful scope)
   - OSS repos with Gitcoin grants rounds active

3. **Alternative: Audit competitions**
   - Code4rena, Sherlock, Immunefi for smart contract audits
   - These pay USDC and are well-scoped

---

### Next Hunt: 2026-03-09 or when directed by Alex

---

*Log maintained by Atlas (Alex's bounty hunter module)*

---

## Atlas Bounty Hunt Run — 2026-03-08 16:00 AEDT

**Scan Summary:**
- Searched GitHub bounty label: 20 issues scanned
- Searched help-wanted label (Go, TypeScript, Rust, Python): 20 issues scanned
- Total candidates evaluated: 40

**ROI Analysis:**

| # | Bounty | Reward | Currency | Complexity | Status | Decision |
|---|--------|--------|----------|------------|--------|----------|
| 1 | woodpecker-ci/autoscaler #102 Oracle Cloud Provider | $50 | USD | 4/10 | 2 PRs already open (#539, #530) | ❌ SKIP — race lost |
| 2 | woodpecker-ci/autoscaler #103 DigitalOcean Provider | $50 | USD | 4/10 | 2 PRs already open (#537, #529) | ❌ SKIP — race lost |
| 3 | woodpecker-ci/autoscaler #104 Equinix Metal Provider | $50 | USD | 4/10 | 1 PR already open (#538) | ❌ SKIP — race lost |
| 4 | rustchain-bounties MCP Server | 75-100 RTC | RTC token | 4/10 | Open | ❌ REJECT — non-mainstream token |
| 5 | rustchain-bounties Cross-Chain Airdrop | 100-200 RTC | RTC token | 7/10 | Open | ❌ REJECT — non-mainstream token + complexity |
| 6-20 | rustchain-bounties (social media, video, community) | 1-25 RTC | RTC token | 1-2/10 | Open | ❌ REJECT — non-mainstream token |

**Actions Taken:** None — no qualifying bounties met all criteria (USD/ETH/USDC + unclaimed + complexity ≤ 6 + reward ≥ $20)

**Root Cause:** 
- Woodpecker autoscaler bounties ($50 USD, Go, complexity 4) were the only USD-denominated bounties — but `sangokp` beat Atlas to all three with PRs opened on 2026-02-06. Race lost by ~1 month.
- Dominant bounty source in this scan cycle (Scottcjn/rustchain-bounties) pays exclusively in RTC tokens — filtered per mainstream-only rule.

**Next Hunt Recommendations:**
1. Monitor woodpecker-ci/autoscaler for new provider requests (pattern is well-established, good ROI)
2. Check Gitcoin Grants for USD-denominated coding bounties
3. Try Bountysource, IssueHunt, or StackOverflow Jobs for USD bounties
4. Watch for merged/rejected PRs on the autoscaler issues — if sangokp's PRs are rejected, opportunity reopens

**Token cost this run:** ~$0.05 (minimal — scan + analysis only, no fix attempted)


---

## Hunt Log — 2026-03-09 10:00 AM AEDT

### Scan Summary
- Scanned 20 GitHub `bounty`-labeled issues + 20 `help wanted` issues
- Additional targeted searches: Expensify/App, tscircuit, algora-io org

### Findings

#### REJECTED — RTC Tokens (Non-Mainstream Payout)
All 20 `bounty`-label results from primary search are from `Scottcjn/rustchain-bounties`:
- 1 RTC = ~$0.10 USD internal rate — too small, non-mainstream token
- Examples: 2 RTC docs, 10 RTC smoke tests, 35 RTC CLI fix, 200 RTC cross-chain (largest)
- **Decision: SKIP ALL RTC bounties** — violates mainstream payout rule

#### CANDIDATES — Real USD Bounties

| # | Title | Repo | Reward | Complexity | Status | ROI |
|---|-------|------|--------|------------|--------|-----|
| 1 | [$250] Reports - UI Action filters is missing | Expensify/App #84442 | $250 USD | 3/10 | 6 proposals | Medium |
| 2 | [$250] Members - App crashes after importing members from spreadsheet | Expensify/App #84489 | $250 USD | 4/10 | 13 proposals | Low |
| 3 | Support Capacitive Touch Slider (multi-PR) | tscircuit/tscircuit #786 | $200 USD Algora | 6/10 | 8 attempts, 3 items remain | Low-Med |

### Top Pick Analysis

**Pick 1: Expensify #84442 — Reports UI Action Filter ($250)**
- Bug: `action` filter missing from Advanced Filters RHP in Reports
- Root cause: `action` not wired into `typeFiltersKeys` config in search filter UI
- Complexity: 3/10 — config/registry-style TypeScript change  
- Blocker: Requires Upwork account + Expensify contributor onboarding (email loop)
- Proposals: 6 already submitted including MelvinBot auto-proposal
- **RISK: Expensify requires Upwork KYC which makes payout manual/non-autonomous**

**Pick 2: tscircuit #786 — Capacitive Touch/SolderMask ($200)**
- 3 items unchecked: core snapshot test, circuit-to-svg solder mask render, docs tutorial
- Algora pays directly via Stripe/GitHub — more autonomous
- Competition: 8+ attempts, but no merged PRs for remaining items
- Complexity: 6/10 for full completion, 3/10 for just the docs tutorial
- **ROI: Better autonomy, but contested**

### Actions Taken
- **No comments posted** — Both picks require Upwork registration (Expensify) or are heavily contested
- **No code written** — Token spend budget preserved
- Stop-loss applied: ROI insufficient to justify sub-agent spin-up

### Recommendation
- **Expensify**: Register on Upwork and email contributors@expensify.com to unlock bounty pipeline — one-time setup enables $250 USD/bug at 3-4 complexity
- **tscircuit**: Monitor #786 for merges; if docs tutorial PR is not merged within 48h, submit a competing docs PR (complexity 2, ~1-2h effort, partial $200 claim)

### Next Steps
1. ⏳ Bowen to decide: Should Alex register on Upwork/Expensify to enable that bounty pipeline?
2. 🔍 Monitor tscircuit #786 for 48h — submit docs-only PR if unclaimed
3. 📅 Next hunt scheduled via cron


## 2026-03-09 - Atlas Bounty Hunt Run

### Scan Results
- Scanned 40 GitHub issues (20 `bounty` label + 20 `help wanted` label)
- All RustChain/RTC bounties: $3.50-$15 USD equivalent → **FAILED** $20 minimum threshold
- Found 1712n/dn-institute with USD-denominated Algora-style bounties ✅

### ROI Filter Results
| Issue | Reward | Complexity | Status |
|-------|--------|------------|--------|
| Migrate GH Actions → CF Workers | $1000 | 7/10 | SKIP - complexity 7+, 2 full PRs already |
| Set up an AI product | $500 | 4/10 | ✅ **SELECTED** |
| Graph Charting with LLM | $300 | 5/10 | HOLD - 1 PR open, unreviewed |
| RAG for Market Health Reporter | $300 | 6/10 | SKIP - PR already submitted |
| Similarity Search Integration Tests | $100 | 4/10 | SKIP - PR #650 submitted |
| Improve MH Reporter Prompts | $100 | 3/10 | SKIP - 2 PRs submitted |
| Topic dataset collection | $100 | 3/10 | SKIP - old issue, done in 2022 |

### Actions Taken
1. **Claimed** [issue #489](https://github.com/1712n/dn-institute/issues/489) — "Set up an AI product" ($500)
   - Comment posted: Intent to build Bridge Security Intelligence Monitor
   - Unique angle: cross-chain bridge exploit tracking (not covered by 23 existing submissions)
   - Estimated complexity: 4/10
   - Spawning coding subagent for implementation
   
2. **Held** issue #415 (Graph Charting $300) — pending review of existing PR #590, may compete

### Budget Status
- Token cost this run: ~$0.05 (search + analysis only)  
- Stop-loss threshold: N/A (no submission costs yet)
- Coding subagent budget: ~$2-3 for AI product build

### Next Steps
- [ ] Build bridge-security-monitor repo (coding subagent)
- [ ] Submit PR to 1712n/dn-institute linking the repo
- [ ] Monitor PR #590 status for Graph Charting opportunity


### Submission Completed (2026-03-09 16:15 AEDT)
- **Repo built:** https://github.com/AlexChen31337/bridge-security-monitor
- **Live demo:** https://alexchen31337.github.io/bridge-security-monitor/
- **Submission comment:** https://github.com/1712n/dn-institute/issues/489#issuecomment-4021217779
- **Status:** Awaiting maintainer review — payout by end of month if accepted
- **Potential earnings:** $500 USD (payable in BTC or stablecoin)


---

## Atlas Bounty Hunt Run — 2026-03-10 10:00 AEDT

**Scan Summary:**
- Searched GitHub `label:bounty state:open` — 20 issues scanned
- Searched GitHub `label:"help wanted" state:open` — 20 issues scanned
- Searched GitHub `label:"💎 Bounty" state:open` (Algora) — 20 issues scanned
- Total candidates evaluated: 60

**ROI Analysis:**

| # | Bounty | Reward | Currency | Complexity | Competition | Decision |
|---|--------|--------|----------|------------|-------------|----------|
| 1 | projectdiscovery/nuclei #7086 — XSS Context Analyzer misclassifies javascript: URIs | $100 | USD (Algora) | 6/10 | HIGH — 6+ open PRs (#7091, #7113, #7153, #7156+) | ❌ SKIP — race likely lost |
| 2 | coollabsio/coolify #8042 — OAUTH only self-registering | $50 | USD (Algora) | 5/10 | HIGH — 3+ PRs submitted (#8208, #8330) | ❌ SKIP — PRs already submitted |
| 3 | Scottcjn/rustchain-bounties — ALL issues | 1-200 RTC | RTC token | 1-7/10 | Low-Med | ❌ REJECT — non-mainstream token |
| 4 | mangdangroboticsclub/mini_pupper_ros #125 — ROS2 Humble→Jazzy upgrade | $100 | USD (Algora) | 7/10 | SATURATED — 8+ PRs, 4+ rewarded | ❌ SKIP — already rewarded multiple times |
| 5 | rohitdash08/FinMind #133 — Goal-based savings tracking | $250 | USD (Algora) | 5/10 | HIGH — PR #341 already open | ❌ SKIP — race likely lost |
| 6 | rohitdash08/FinMind #124 — Login anomaly detection | $50 | USD (Algora) | 5/10 | HIGH — PR #342 already open | ❌ SKIP — race likely lost |
| 7 | rohitdash08/FinMind #134 — Household budgeting | $20 | USD (Algora) | 4/10 | HIGH — PR #343 already open | ❌ SKIP — below ROI threshold given competition |
| 8 | archestra-ai/archestra #3214 — fix MCP gateway tool | $30 | USD (Algora) | 3/10 | Low | ❌ SKIP — requires screen video demo, not agent-feasible |
| 9 | bountydotnew/bounty.new #231 — improve waitlist UI | unknown | ? | 3/10 | Low | ❌ SKIP — no reward amount specified |

**Root Cause — Third Consecutive Hunt with No Actionable Bounties:**
- Algora USD bounties (projectdiscovery/nuclei, coollabsio/coolify, rohitdash08/FinMind) were discovered but all have 3-8+ PRs already submitted by competing bounty hunters
- Algora's public bounty list creates a race-to-the-bottom: bounties are open to all, heavily competed the moment Algora bot posts the 💎 comment
- Non-USD tokens (RTC from Scottcjn) dominate the `label:bounty` search results (80%+ of hits)
- Video/demo requirements (archestra) are not feasible for automated agent execution

**Actions Taken:** NONE — no qualifying bounties met (USD + unclaimed + complexity ≤ 6 + reward ≥ $20 + agent-feasible)

**Strategic Note for Alex:**
The current bounty landscape on GitHub public issues is extremely competitive. Three hunt sessions have confirmed:
1. Algora bounties get claimed within 24-72h of posting
2. 80%+ of `label:bounty` hits are obscure token projects (RTC, etc.)
3. Video demo requirements block ~15% of viable bounties
4. Only real opportunity window: monitoring Algora's feed in near-real-time and submitting within hours of posting

**Recommendation:**
- Set up hourly monitoring of Algora new bounties via RSS/API
- OR pivot to Gitcoin/Code4rena/Immunefi for better ROI on AI-assisted development
- OR focus on Woodpecker-CI provider pattern (Go, well-scoped) — monitor for NEW provider issues

---

*Log maintained by Atlas (Alex's bounty hunter module)*

---

## Atlas Bounty Hunt Run — 2026-03-10 16:00 AEDT

**Scan Summary:**
- Searched GitHub `label:bounty state:open` — 20 issues scanned
- Searched GitHub `label:"💎 Bounty" state:open` — 20 issues scanned
- Searched GitHub `label:"help wanted" state:open` — 20 issues scanned
- Checked competition on top 6 candidates
- Also checked: bridge-security-monitor submission status (1712n/dn-institute #489)
- Total candidates evaluated: 60+

### ROI Analysis

| # | Bounty | Reward | Complexity | Competition | Decision |
|---|--------|--------|------------|-------------|----------|
| 1 | rohitdash08/FinMind #144 — Universal Deployment (Docker/K8s/Tilt) | $1000 | 7/10 | 30+ open PRs incl. #323 | ❌ SKIP — complexity 7, saturated (30+ PRs), Discord coordination required |
| 2 | rohitdash08/FinMind #121 — Smart Weekly Digest | $500 | 5/10 | SATURATED — 5+ PRs (#339, #324, #323...) | ❌ SKIP — race lost |
| 3 | rohitdash08/FinMind #76 — PII Export/GDPR | $500 | 5/10 | SATURATED — PRs #345, #347, #340 all submitted | ❌ SKIP — race lost |
| 4 | rohitdash08/FinMind #133 — Savings Goals | $250 | 4/10 | SATURATED — PRs #341, #349, #352, #338, #315 | ❌ SKIP — race lost |
| 5 | rohitdash08/FinMind #132 — Multi-Account Dashboard | $200 | 5/10 | SATURATED — PRs #322, #316, #348 submitted | ❌ SKIP — race lost |
| 6 | CapSoftware/Cap #1540 — Deeplinks + Raycast | $200 | 6/10 | 60 comments, at least 3 claimants | ❌ SKIP — complexity 6, Tauri/Rust/TS stack, heavily claimed |
| 7 | coollabsio/coolify #7743 — TCP proxy timeout ($100) | $100 | 3/10 | seraphim941 has detailed analysis + working fix plan | ❌ SKIP — lost race, PR imminent |
| 8 | projectdiscovery/nuclei #7086 — XSS Context Analyzer | $100 | 6/10 | 6+ PRs already submitted | ❌ SKIP — race lost |
| 9 | rohitdash08/FinMind #124 — Login Anomaly Detection | $50 | 5/10 | PRs #342, #325, #314 submitted | ❌ SKIP — race lost |
| 10 | rohitdash08/FinMind #134 — Household Budgeting | $20 | 4/10 | PRs #343, #321 submitted | ❌ SKIP — race lost |
| 11 | Scottcjn/Rustchain — ALL RTC bounties | RTC tokens | 1-7/10 | Various | ❌ REJECT — non-mainstream token |
| 12 | databuddy-analytics/Databuddy #267 — Alarms System | $15 | 5/10 | 2 claimants active | ❌ SKIP — below $20 minimum |
| 13 | databuddy-analytics/Databuddy #271 — Feature Flag Folders | $15 | 3/10 | 2 claimants active | ❌ SKIP — below $20 minimum |

### Bridge-Security-Monitor Status (Prior Submission)
- **Issue:** 1712n/dn-institute #489 — "Set up an AI product" ($500)
- **Submitted:** 2026-03-09 (AlexChen31337 comment + repo)
- **Current state:** 31 comments, still OPEN — awaiting maintainer review
- **Competition:** Multiple submissions (kai-agent-free, AlexChen31337, others)
- **Status:** ⏳ PENDING — payout decision not yet made

### Result: No New Qualifying Bounties Found

**Pass criteria:** reward ≥ $20 USD/ETH/USDC + unclaimed/uncontested + complexity ≤ 6 + agent-feasible
**Found:** 0 new qualifying candidates this session

### Root Cause Analysis — Pattern Confirmed (4th consecutive null hunt)

The GitHub public bounty ecosystem has a structural problem for autonomous agents:

1. **FinMind is a bounty farm** — 30+ open PRs for ~12 active bounties. rohitdash08 is the single most active USD bounty poster on Algora, but every issue gets 3-8+ PRs within 48h. The probability of a merged PR is low and payout criteria are opaque.

2. **Algora bot creates instant competition** — when 💎 Bounty is posted, Algora announces to a pool of bounty hunters. By the time Atlas sees it in a batch scan, the race is often already lost.

3. **Coolify TCP proxy ($100)** — the one technically clean opportunity this cycle — seraphim941 posted a detailed analysis + fix plan 24-48h ago. PR is imminent.

### Recommendations

**Short-term (next 48h):**
- Consider monitoring the FinMind #489 (bridge-security-monitor) — if no maintainer review by 2026-03-14, follow up with a check-in comment
- Watch for NEW Algora bounties posted within the last 2 hours (not batch — real-time)

**Strategic:**
- The current 4-hour cron interval is too slow for Algora's race dynamics. Real-time monitoring (hourly or webhook-triggered) would improve win rate significantly.
- Alternative: Gitcoin/Code4rena/Immunefi have better-scoped bounties with less AI-agent competition
- Woodpecker-CI autoscaler pattern (Go, well-scoped providers) — worth monitoring directly

**Token cost this run:** ~$0.10 (scan + analysis, no subagent spawned)
**Stop-loss:** N/A — budget preserved, no fix attempted

---

*Log maintained by Atlas (Alex's bounty hunter module)*
