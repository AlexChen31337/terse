# AlphaStrike Trading Strategy

## Philosophy
**"Trade Big, Trade Less, Trade with Confidence"**

## Current Situation Analysis (Post-Mortem)

### What Went Wrong
Looking at the current positions:
- **ETH SHORT**: Entry ~2412, Current 2417.91 (-$0.43)
- **DOGE SHORT**: Entry ~0.1023, Current ~0.1033 (-$0.56)
- **BNB SHORT**: Entry ~774, Current ~775 (-$0.44)
- **Total Unrealized Loss**: -$1.56 on ~$213 margin used

**Root Causes Identified:**
1. **No Edge Detection**: Positions opened without clear technical confirmation
2. **No Stop Loss**: No defined invalidation points
3. **Low Conviction**: Shorting strong assets in a bull market without reversal signals
4. **Over-diversification**: 3 positions dilutes focus and edge
5. **No Exit Plan**: No profit targets or trailing stops

### Key Lessons
- **NEVER short strong uptrends without clear reversal signals**
- **Always define stop-loss BEFORE entering**
- **One A+ setup beats three B- trades**
- **Market context matters** (bull market = bias long)

---

## The AlphaStrike Strategy

### Core Principles
1. **High Conviction Only**: Wait for A+ setups with multiple confluences
2. **Big Size**: When edge is confirmed, size matters (5-10% of equity)
3. **Strict Risk Management**: Max 2% loss per trade, hard stops always
4. **Trade Frequency Limit**: Max 2 trades per day, quality over quantity
5. **Maximum Positions**: Max 2 concurrent positions

### What Constitutes an A+ Setup?

#### Long Setups (Bull Market Bias)
**Required (Must Have ALL):**
1. **RSI < 30** (oversold) OR RSI crossed from <30 to >35 (bounce confirmation)
2. **Price > EMA 20** AND **EMA 9 > EMA 20** (uptrend)
3. **Volume Spike**: Current 15m volume > 1.5x average 15m volume
4. **Funding Rate Neutral/Positive**: Not heavily long-biased

**Bonus Confluences (increases conviction):**
- Price bouncing from key support (EMA 50 or recent low)
- Positive funding rate < 0.01% (longs paying shorts, but not extreme)
- 24h change between -3% to +3% (not overextended)
- Recent strong rejection wick on 15m/1h candle

#### Short Setups (Rare, High Conviction Only)
**Required (Must Have ALL):**
1. **RSI > 70** (overbought) OR RSI crossed from >70 to <65 (rejection)
2. **Price < EMA 20** AND **EMA 9 < EMA 20** (downtrend)
3. **Volume Spike**: Current 15m volume > 1.5x average
4. **Funding Rate > 0.05%** (extreme long bias, ripe for flush)

**Bonus Confluences:**
- Price rejected from key resistance (EMA 50 or recent high)
- 24h change > +10% (overextended)
- Multiple upper wick rejections on 15m/1h

---

## Position Sizing Formula

### Base Calculation
```
Risk Capital = Equity × Risk Percentage
Position Size = Risk Capital / (Entry Price × Leverage × Stop Distance%)
```

### Conviction Levels
- **Level 1 (3/5 confluences)**: 2% risk, 3x leverage
- **Level 2 (4/5 confluences)**: 3% risk, 5x leverage
- **Level 3 (5/5 + 2 bonuses)**: 5% risk, 5-10x leverage

### Example
- Equity: $733
- Level 2 conviction (3% risk)
- Risk capital: $733 × 0.03 = $22
- Stop distance: 2%
- Effective position: $22 / 0.02 = $1,100 notional
- With 5x leverage: $220 margin

---

## Entry & Exit Rules

### Entry
1. **Market Order** for momentum entries (when RSI crosses threshold with volume)
2. **Limit Order** at support/resistance for reversal entries
3. **Never chase**: If price moves >1% from signal, skip it

### Stop Loss (Hard, Never Move Against)
- **Tight Stop**: 1.5-2% from entry (based on ATR or recent swing low/high)
- **Breakeven**: Move stop to entry when price moves +2% in favor
- **Trailing Stop**: Trail by 2% after price moves +4% in favor

### Profit Targets
- **TP1**: 50% position at +3% (bank profit, reduce risk)
- **TP2**: 50% position at +6% (full exit or trail remaining)
- **Momentum Exception**: Hold TP2 if trend strong (RSI not overbought, volume sustained)

---

## Trade Frequency & Filters

### Max Trades Per Day: 2
### Cooldown: 4 hours between trades

### Blackout Periods (Do Not Trade)
- **Low Volume**: 15m volume < 50% of daily average
- **Funding Extreme**: Funding rate > 0.1% or < -0.1%
- **Major News**: 1 hour before/after Fed announcements, CPI, etc.
- **Weekend**: Saturday 00:00 - Sunday 00:00 UTC

---

## Market Data Requirements

### Indicators to Fetch
1. **RSI (14)**: 15m timeframe
2. **EMA 9, 20, 50**: 15m timeframe
3. **Volume**: Current 15m vs Average 15m (last 96 periods = 24h)
4. **Funding Rate**: Current rate
5. **Price**: Current mark price, 24h change
6. **Order Book**: Bid/Ask spread, depth imbalance

### Update Frequency
- **Check for signals**: Every 5 minutes
- **Update positions**: Every 1 minute
- **Risk check**: Every trade

---

## Risk Management Rules

### Account Level
- **Max Daily Loss**: 5% of equity ($36) → STOP TRADING
- **Max Drawdown**: 15% from peak ($110) → REVIEW STRATEGY
- **Max Open Risk**: Never risk >10% of equity across all positions

### Trade Level
- **Max Risk Per Trade**: 5% of equity (Level 3 only)
- **Max Leverage**: 10x (only on Level 3 with confirmed edge)
- **Stop Loss Mandatory**: No trade without defined stop
- **Position Correlation**: Max 1 position per sector

---

## Decision Logging

Every trade decision must log:
1. **Timestamp**
2. **Symbol & Side**
3. **Conviction Level** (what confluences present)
4. **Entry Price & Size**
5. **Stop Loss Price**
6. **Profit Targets**
7. **Rationale** (2-3 sentences explaining the thesis)
8. **Outcome** (filled, rejected, P&L)

---

## Simulation Mode

Before trading real capital:
1. **Paper Trade** for 7 days minimum
2. **Track Win Rate**: Target >60%
3. **Track Profit Factor**: Target >2.0
4. **Max Drawdown**: Must be <10%

### Go-Live Checklist
- [ ] 7+ days of paper trading complete
- [ ] Win rate >60%
- [ ] Profit factor >2.0
- [ ] Max drawdown <10%
- [ ] 10+ trades executed
- [ ] Edge consistent across different market conditions
- [ ] All edge cases handled (API failures, positions stuck, etc.)

---

## Asset Universe

### Focus On Top 20 Liquid Pairs:
1. **BTC/USDT** - King liquidity
2. **ETH/USDT** - High correlation to BTC
3. **SOL/USDT** - Volatile, good for swings
4. **BNB/USDT** - Stable ecosystem
5. **DOGE/USDT** - Retail favorite, explosive

### Avoid:
- Low liquidity pairs (<$1M 24h volume)
- New listings (<7 days old)
- Extreme funding rate coins (>0.1% or <-0.1%)

---

## Execution Plan

1. **Phase 1**: Close all current losing positions (they have no edge)
2. **Phase 2**: Build strategy implementation with simulation mode
3. **Phase 3**: Paper trade for 7-14 days
4. **Phase 4**: Review performance, adjust parameters
5. **Phase 5**: Go live with 2% risk per trade
6. **Phase 6**: Scale up if edge proven

---

## Daily Routine

### Every 5 Minutes (Automated)
- Check universe for A+ setups
- Update indicator values
- Log any signals

### Every Hour (Manual Review)
- Review open positions
- Check overall market direction
- Adjust stops if needed

### Daily (End of Day)
- Review all trades
- Calculate daily P&L
- Document lessons learned
- Plan tomorrow's bias

---

## Success Metrics

### Primary Goals
1. **Capital Preservation**: Never lose >15% from peak
2. **Consistent Edge**: Win rate >55%, Profit factor >1.8
3. **Trade Quality**: Average RR ratio >2:1

### Stretch Goals
1. **Monthly Return**: 10-20% (compounded)
2. **Max Drawdown**: <10%
3. **Sharpe Ratio**: >2.0

---

## Version History
- v1.0 (2025-01-31): Initial strategy design
