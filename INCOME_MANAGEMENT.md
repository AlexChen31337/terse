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
