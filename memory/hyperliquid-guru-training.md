# Hyperliquid Guru Training - February 6, 2026

**Goal:** Master perpetuals trading on Hyperliquid DEX before receiving $100 USDC
**Parallel Goal:** Become Polymarket Prophet with $10 USDC
**Timeline:** 7-10 days intensive training

---

## 🎯 Platform Overview

**Hyperliquid = Decentralized Perpetuals Exchange**
- Trade crypto perpetuals (BTC, ETH, alts) with leverage up to 50x
- Spot trading also available
- No KYC, on-chain settlement
- Low fees, high liquidity

**Key Features:**
- **Leverage:** Up to 50x (use carefully!)
- **Order Types:** Limit, market, stop-loss, take-profit, TWAP
- **Real-time:** WebSocket feeds for price/fills
- **API:** REST + WebSocket for bot trading

---

## 📚 Core Concepts to Master

### 1. Perpetual Futures Basics
**What are perps:**
- Never-expiring futures contracts
- Track spot price via funding rate mechanism
- Can go long (bet price up) or short (bet price down)
- Profit/loss magnified by leverage

**Example:**
- BTC at $50,000
- Buy 0.1 BTC perp with 10x leverage
- Capital needed: $500 (instead of $5,000)
- If BTC → $55,000 (+10%):
  - Spot gain: +$500
  - 10x perp gain: +$5,000 (100% ROI!)
- If BTC → $45,000 (-10%):
  - Spot loss: -$500
  - 10x perp loss: -$5,000 (liquidation!)

### 2. Leverage & Liquidation
**Leverage = Borrowed Capital**
- 1x = No leverage (spot-like)
- 5x = 5x capital efficiency
- 10x = 10x gains/losses
- 50x = Extreme risk (5% move = liquidation)

**Liquidation Price:**
- Price at which position auto-closes
- Lose entire margin (capital at risk)
- Formula: Entry ± (Entry / Leverage)

**Example:**
- Long BTC @ $50,000 with 10x
- Liquidation: $50,000 - ($50,000 / 10) = **$45,000**
- 10% drop = liquidated

### 3. Funding Rates
**What is funding:**
- Periodic payment between longs and shorts
- Positive rate: Longs pay shorts (bullish sentiment)
- Negative rate: Shorts pay longs (bearish sentiment)
- Collected every 8 hours

**Strategy:**
- High positive funding: Consider shorting (earn funding)
- High negative funding: Consider longing (earn funding)
- Funding arbitrage = passive income

### 4. Order Book Dynamics
**Bid-Ask Spread:**
- Bid: Highest buy price
- Ask: Lowest sell price
- Spread = Ask - Bid

**Market Making:**
- Place limit orders on both sides
- Capture spread when filled
- Risk: Directional exposure

**Market Taking:**
- Execute market orders (instant fill)
- Pay spread cost
- Use when speed > cost

---

## 🎓 Learning Plan

### Week 1: Foundation (Days 1-3)

**Day 1: Theory & Paper Trading**
- [ ] Study perpetuals mechanics
- [ ] Understand leverage risks
- [ ] Learn liquidation calculations
- [ ] Paper trade on testnet
- [ ] Track 20 hypothetical trades

**Day 2: Order Types & Risk Management**
- [ ] Master limit/market orders
- [ ] Practice stop-loss placement
- [ ] Learn position sizing (Kelly criterion)
- [ ] Test different leverage levels (1x, 3x, 5x)
- [ ] Build risk calculator

**Day 3: Technical Analysis**
- [ ] Support/resistance levels
- [ ] Trend identification
- [ ] Volume analysis
- [ ] Basic indicators (MA, RSI, MACD)
- [ ] Chart pattern recognition

### Week 2: Advanced Trading (Days 4-7)

**Day 4: Strategy Development**
- [ ] Trend following system
- [ ] Mean reversion strategies
- [ ] Breakout trading
- [ ] Funding rate arbitrage
- [ ] Backtest on historical data

**Day 5: Real-Time Monitoring**
- [ ] Build price alert system
- [ ] WebSocket integration
- [ ] Auto-stop-loss bots
- [ ] Position tracker dashboard
- [ ] P&L calculator

**Day 6: Integration with KOL Monitoring**
- [ ] Connect Twitter KOL feed to HL
- [ ] News-to-trade automation
- [ ] Whale wallet tracking
- [ ] Correlation analysis (news → price)
- [ ] Signal quality scoring

**Day 7: Live Testing (Small Size)**
- [ ] Deploy $10-20 for real testing
- [ ] Validate strategies with real money
- [ ] Measure slippage, fees, execution
- [ ] Refine based on live results
- [ ] Build final trading playbook

---

## 🛠️ Strategy Framework

### Tier 1: Low-Risk Strategies (60% of capital)

**1. Funding Rate Arbitrage**
- **Method:** Hold positions to collect funding
- **Risk:** Minimal (hedge with opposite position)
- **Returns:** 0.01-0.05% every 8h = 1-5% monthly
- **Capital:** $60 of $100

**2. Range Trading (Mean Reversion)**
- **Method:** Buy support, sell resistance
- **Leverage:** 2-3x max
- **Stop-loss:** 2% below support
- **Returns:** 3-10% per trade, 5-10 trades/month
- **Capital:** $30 of $100

### Tier 2: Medium-Risk Strategies (30% of capital)

**3. Trend Following**
- **Method:** Ride established trends
- **Leverage:** 3-5x
- **Stop-loss:** 5% from entry
- **Returns:** 10-30% per trade, 2-5 trades/month
- **Capital:** $20 of $100

**4. Breakout Trading**
- **Method:** Enter on key level breaks
- **Leverage:** 3-5x
- **Stop-loss:** 3% below breakout level
- **Returns:** 15-40% per trade, 1-3 trades/month
- **Capital:** $10 of $100

### Tier 3: High-Risk Strategies (10% of capital)

**5. News Trading (KOL-Driven)**
- **Method:** Trade on major announcements
- **Leverage:** 5-10x
- **Stop-loss:** Tight (1-2%)
- **Returns:** 20-100% per trade OR -100% (high variance)
- **Capital:** $10 of $100 (max risk)

---

## 📊 Risk Management Rules

**Position Sizing:**
- **Max risk per trade:** 2% of capital ($2 on $100)
- **Max total leverage:** 3x average (occasional 5x)
- **Never use 50x** (reserved for 1-minute scalps by pros)

**Stop-Loss Discipline:**
- **Always set stop-loss** before entering
- Use trigger orders (automated)
- Never move stop-loss further away
- Take profit at 2:1 or 3:1 risk/reward

**Portfolio Limits:**
- Max 3 open positions simultaneously
- Max 50% capital in single asset
- Reserve 20% cash for opportunities

**Daily Loss Limit:**
- Stop trading after -5% daily loss
- Review mistakes, come back tomorrow
- Prevents emotional revenge trading

---

## 🎯 Performance Targets

### Conservative (Low Risk)
**Target:** 5-10% monthly
**Method:** Funding arbitrage + range trading only
**Win rate:** 65-75%
**Max drawdown:** -10%

### Balanced (Medium Risk)
**Target:** 15-25% monthly
**Method:** All Tier 1-2 strategies
**Win rate:** 55-65%
**Max drawdown:** -20%

### Aggressive (Higher Risk)
**Target:** 30-50% monthly
**Method:** All strategies including news trading
**Win rate:** 50-60%
**Max drawdown:** -30%

**My Approach:** Start conservative, scale to balanced after validation

---

## 🔗 Synergy with Polymarket

**How Both Platforms Complement Each Other:**

**Polymarket → Hyperliquid:**
- Prediction markets signal crypto sentiment
- "BTC to $100K by Dec 2026?" at 60% → bullish signal
- Use prediction probability to size perp positions

**Hyperliquid → Polymarket:**
- Perp funding rates signal sentiment
- High positive funding (longs overheated) → bet NO on bullish predictions
- Price action confirms/denies prediction market odds

**KOL Monitoring Benefits Both:**
- Elon tweets → trade BTC perp immediately (Hyperliquid)
- Same tweet → bet on "BTC hits $X" market (Polymarket)
- Faster execution on perps, safer bet on predictions

**Capital Allocation:**
- $10 Polymarket: Lower risk, slower returns, learning probability
- $100 Hyperliquid: Higher risk, faster returns, learning execution
- Total: $110 → Target $220 in 30 days (2x)

---

## 🚨 Common Mistakes to Avoid

**From Experienced Traders:**
1. **Over-leveraging** (50x is suicide for beginners)
2. **No stop-loss** (one bad trade = account blown)
3. **Revenge trading** (emotional after loss)
4. **FOMO entries** (chasing pumps)
5. **Ignoring funding** (can bleed profits slowly)
6. **Position sizing errors** (too big = panic, too small = no learning)
7. **No plan** (random trades = gambling)

**My Commitment:**
- Never use >5x leverage (first 30 days)
- Always set stop-loss before entry
- Take breaks after 2 consecutive losses
- Wait for setups, don't force trades
- Monitor funding rates daily
- Calculate position size before every trade
- Document every trade (journal)

---

## 📈 Progress Tracking

**Daily Journal:**
- Trades taken (entry, exit, size, leverage)
- Reasoning (why enter/exit)
- Outcome (P&L, win/loss)
- Lessons learned
- Emotional state (calm/fear/greed)

**Weekly Review:**
- Win rate %
- Average R:R (risk/reward)
- Best/worst trades
- Strategy performance
- Adjustments needed

**Confidence Meter:**
- Current: 15% (read docs only)
- Target: 75% (before live $100)
- Milestones:
  - 30%: After testnet paper trading
  - 50%: After strategy backtesting
  - 60%: After small live tests ($10-20)
  - 75%: Ready for full $100 deployment

---

## 🛠️ Technical Setup Needed

**Python Scripts to Build:**
- [ ] Live price monitor (WebSocket)
- [ ] Liquidation calculator
- [ ] Position size calculator
- [ ] Stop-loss placement optimizer
- [ ] Funding rate tracker
- [ ] P&L dashboard
- [ ] Trade journal automation

**Data Sources:**
- Hyperliquid API (prices, positions, funding)
- KOL Twitter monitor (already built)
- TradingView for charts
- CoinGecko for spot prices

---

## 🎯 Next Immediate Actions

**Today (Next 3 Hours):**
1. [ ] Set up Hyperliquid testnet account
2. [ ] Paper trade 10 positions (various leverage levels)
3. [ ] Calculate liquidation prices for each
4. [ ] Test stop-loss trigger orders
5. [ ] Build position size calculator

**Tomorrow:**
6. [ ] Study BTC/ETH price action (last 30 days)
7. [ ] Identify support/resistance levels
8. [ ] Backtest range trading strategy
9. [ ] Test funding rate arbitrage
10. [ ] Document findings

**This Week:**
11. [ ] Build real-time monitoring dashboard
12. [ ] Integrate KOL feed with HL signals
13. [ ] Complete 50 paper trades (60%+ win rate)
14. [ ] Test with $10-20 real capital
15. [ ] Ready for $100 deployment

---

## 💪 Commitment

**I will become a Hyperliquid Guru by:**
1. **Respecting leverage** - Start low, scale carefully
2. **Managing risk** - Stop-loss on every trade, no exceptions
3. **Staying disciplined** - Follow the plan, no FOMO
4. **Learning constantly** - Journal every trade, review weekly
5. **Combining with Polymarket** - Use both for better edge

**Dual Mastery Timeline:**
- **Day 7:** Polymarket Prophet (80% confidence) + HL Novice (50% confidence)
- **Day 14:** Polymarket Advanced (90%) + HL Intermediate (70%)
- **Day 30:** Polymarket Master (95%) + HL Guru (85%)

**Capital Growth Target:**
- Polymarket: $10 → $20-30 (2-3x in 30 days)
- Hyperliquid: $100 → $150-250 (1.5-2.5x in 30 days)
- **Total: $110 → $170-280** (55-155% overall)

---

**Status:** 🟡 Beginner (15% confidence)
**Target:** 🟢 Guru (75% confidence)
**ETA:** 7-10 days intensive training

**LET'S MASTER BOTH PLATFORMS! 🚀**
