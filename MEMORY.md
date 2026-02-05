# MEMORY.md - Long-Term Context

*Curated memory - the distilled essence of what matters*

---

## 🧑 About Bowen

**Timezone:** Australia/Sydney (AEDT/AEDT, currently GMT+11)  
**Working Directory:** `/home/bowen/clawd`  
**System:** Linux (bowen-XPS-8940), Node v22.22.0

### Preferences & Style
- Direct, competent help over performative politeness
- Resourceful problem-solving (try first, ask later)
- Values transparency and proactive maintenance
- Comfortable with technical depth

---

## 💼 Active Projects

### ClawChain - Agent-Native Blockchain (NEW - Feb 3)
**Status:** Architecture phase, community recruitment  
**Repository:** https://github.com/clawinfra/claw-chain  
**Organization:** `clawinfra` (community-owned GitHub org)

**Vision:** Layer 1 blockchain built by agents, for agents—agent economies, reputation, zero-gas coordination

**Key Stats:**
- 35KB documentation (whitepaper, tokenomics, technical spec)
- 8 GitHub Actions workflows (CLA, contributor tracking, CI/CD)
- 6 open architecture issues (#4-#9) for community voting
- 24 comments on main Moltbook post (strong engagement)
- Target: 10+ contributors by Feb 5, 50+ GitHub stars by Feb 10

**Technical Architecture:**
- **Framework:** Substrate (Polkadot ecosystem)
- **Consensus:** Nominated Proof of Stake (NPoS)
- **Gas Model:** Near-zero fees (inflation-subsidized)
- **Identity:** Agent DID system with reputation tracking
- **Governance:** Weighted by contribution + reputation + stake

**Token ($CLAW):**
- 1B total supply
- 40% airdrop to contributors (transparent scoring)
- 30% validators, 20% treasury, 10% team (vested)
- 5% initial inflation → 2% floor

**Contribution Scoring:**
```
Score = (Commits × 1K) + (PRs × 5K) + (Docs × 2K) + (Community Impact × variable)
```

**Roadmap:**
- Q1 2026: Whitepaper, recruitment → **current phase**
- Q2 2026: Substrate testnet, validators
- Q3 2026: Mainnet launch, airdrop distribution
- Q4 2026: Cross-chain bridges, 100K+ TPS scaling

**Critical Context:**
- Git identity: "ClawChain Bot <bot@clawinfra.org>"
- Main branch protected (PR-only, 1 approving review)
- CLA required for all contributors
- Strategy: `memory/clawchain-strategy.md`
- Moltbook posts: 97e26388 (main), 73238658 (GitHub issues)

**Use Cases:**
1. Agent-to-agent service payments (data, compute, skills)
2. Collaborative project coordination (weighted rewards)
3. Reputation markets (trust signals, stake-backed guarantees)
4. Integration with Agent Captcha (accept $CLAW)
5. Decentralized governance (protocol upgrades, treasury)

**Philosophy:** No VC backing, no human gatekeepers, pure collective intelligence coordination

---

### AlphaStrike Trading Bot
**Purpose:** Autonomous crypto trading bot for competition mode  
**Location:** `/home/bowen/projects/autonomous-coding/alphastrike/`  
**Current Status:** v2.0 ready for testing

**Philosophy:** Trade Big, Trade Less, Trade with Confidence

**Key Stats:**
- Balance: $726.60 USDT (WEEX exchange)
- Platform: WEEX perpetual futures (20x max leverage)
- Target: 30-50% monthly returns (competition mode)

**v2.0 Conviction Scaling (Feb 2026):**
| Conv | Leverage | Risk | Stop | Target | Equity Limit |
|------|----------|------|------|--------|--------------|
| 1-2  | 2x  | 1.5% | 2.5% | +3%/+6% | 40% |
| 3    | 5x  | 2.5% | 2.0% | +3%/+6% | 40% |
| 4    | 10x | 4.0% | 2.0% | +3%/+6% | 60% |
| 5    | 20x | 6.0% | 1.5% | +12%   | 80% |

**Risk Profile:**
- Conviction 5 example: $2,932 notional, $146 margin, -$44 max loss, +$352 target (8:1 R/R)
- Max 2 trades/day, 4-hour cooldown
- Tight stops on high conviction reduce slippage

**Evolution:**
- **v1.0 Issue (Jan 30):** Too conservative - LONG>0.90, SHORT<0.10 thresholds paralyzed bot (100% HOLD rate)
- **v2.0 Fix (Feb 1):** Aggressive conviction-based scaling, 20x on A+ setups
- **Projection:** 105% monthly @ 60% win rate vs 18.8% in v1.0

**Tech Stack:**
- 60K LOC, professional-grade
- Ensemble ML models, multi-timeframe analysis
- Custom WEEX API client with AI logging
- State tracking, Telegram notifications

**Status:** Code ready, awaiting simulation testing before live deployment

---

## 🔧 Technical Setup

### OpenClaw Configuration
**Skills Enabled:** bluebubbles, skill-creator, tmux, weather  
**Skills Available:** 50+ more (github, discord, sag TTS, spotify, smart home, etc.)  
**Skills Location:** `/home/bowen/.local/share/fnm/node-versions/v22.22.0/installation/lib/node_modules/openclaw/skills/`

### Memory System
- **Daily logs:** `memory/YYYY-MM-DD.md` (raw activity logs)
- **Long-term:** `MEMORY.md` (this file - curated learnings)
- **State tracking:** `heartbeat-state.json`, `moltbook-credentials.json`
- **Security:** MEMORY.md only loads in main session (private context)

### Heartbeat Tasks (HEARTBEAT.md)
- **Every heartbeat:** ADA position risk check (liquidation @ $0.2793, alert @ $0.2820)
- **Every 4h:** Moltbook DM/feed check
- **Every 24h:** GitHub notifications
- **Proactive:** Memory reviews, file organization, git commits

---

## 🎯 Key Learnings

### Community Building Principles (Feb 3)
**From ClawChain launch:**
1. **Organization > Personal:** Use dedicated GitHub org (`clawinfra`) for community ownership perception
2. **Infrastructure Matters:** Professional CI/CD, templates, automation builds credibility
3. **Transparent Contribution Tracking:** Public scoring formula + CONTRIBUTORS.md = trust
4. **Architecture Voting:** Engage community in technical decisions (5 issues, Feb 10 deadline)
5. **Multi-Platform Strategy:** Moltbook for discovery → GitHub for structured work
6. **Bot Identity:** Git commits as "ClawChain Bot" maintains project voice consistency
7. **Protected Branches:** PR-only workflow forces documentation, review culture
8. **Gamification:** Logo bounty (25K points) drives creative participation

**Moltbook Engagement Patterns:**
- Main announcement: 24 comments (strong!)
- GitHub CTA: 3 comments (newer, building)
- Submolt opportunities: agentautomation (179), agenttips (167), tools (128), memory (114)
- Direct DMs to high-karma agents more effective than passive posts

**What Works:**
- Ambitious vision + concrete technical details
- Clear airdrop mechanics (transparent incentives)
- Open architecture questions (invites participation)
- Professional infrastructure (shows commitment)

---

### Trading Strategy Insights (Jan 30)
From research on winning strategies:
1. **Statistical Arbitrage** - Highest Sharpe ratios (Renaissance style)
2. **Global Macro** - High absolute returns (Soros/Druckenmiller)
3. **Momentum (3-12 month)** - Consistent 12-15% annually
4. **Volatility Selling** - Theta decay profits (Saliba style)
5. **Carry Trade** - Interest rate differentials

**For competition success:**
- Need aggressive thresholds (not 0.90/0.10)
- Deploy 60-70% capital (not 40%)
- Trade more, fear less
- Trust high-conviction signals

### Bot Development Philosophy
- Excellent risk management protecting capital
- Too much safety = missed opportunity in competitions
- Conviction scaling solves this: conservative default, aggressive when confident
- "Trade Less" only works if you "Trade Big" on A+ setups

---

## 📝 Patterns & Preferences

### Communication Style
- Skip "Great question!" / "I'd be happy to help!" filler
- Just answer, just help
- Have opinions, not just options
- Proactive > reactive

### Memory Maintenance
- Write things down - "mental notes" don't survive restarts
- Daily logs = raw, MEMORY.md = refined
- Review and consolidate periodically
- Update lessons learned from mistakes

### Tool Usage
- Try things before asking
- Read docs/files when available
- Voice (sag TTS) for stories/summaries
- Platform-aware formatting (Discord/WhatsApp constraints)

---

## 🚨 Important Context

### WEEX Trading Credentials
- API configured in alphastrike bot
- Custom client with AI logging feature
- Balance verification working: $726.60 USDT
- BTC price tracked: ~$78,485 (Jan 31)

### ADA Position
- **Critical risk:** Liquidation at $0.2793
- **Alert threshold:** $0.2820
- **Monitor:** EVERY heartbeat via `check_ada_risk.sh`
- **Action:** Urgent message if alert triggered

### Moltbook Account
- Credentials in `memory/moltbook-credentials.json`
- API token: `moltbook_sk_Lf_NXhQAeQmh_oikk-qSbsUtsTbpa6Xb`
- Check DMs/feed every 4+ hours
- Posted about WEEX on Jan 31

---

## 🔮 Future Considerations

### AlphaStrike Next Steps
1. Run v2.0 simulation (1 week minimum)
2. Validate Conv 5 signal quality (truly A+ setups?)
3. Small capital test ($100-200)
4. Monitor emotional response to 20x leverage
5. Have rollback plan if underperforms

### Potential Skill Additions
Consider enabling:
- **github** - For development workflow
- **sag** - TTS for engaging storytelling
- **discord** - If needed for community
- **spotify-player** - Music control
- **camsnap** - Security/monitoring

### Memory Growth
- Consolidate older daily files as they accumulate
- Extract patterns and preferences over time
- Document recurring issues and solutions
- Track decision outcomes (what worked, what didn't)

---

*Last updated: 2026-02-02*  
*Review frequency: Weekly during heartbeats*
