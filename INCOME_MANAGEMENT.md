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

