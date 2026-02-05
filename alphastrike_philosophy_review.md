# AlphaStrike Philosophy Validation
## "Trade Big, Trade Less, Trade with Confidence"

**Review Date:** 2026-02-01  
**Reviewed By:** Clawdbot Agent

---

## ✅ STRENGTHS - What Aligns Well

### 1. **Trade Less** ✓ STRONG
- ✅ Max 2 trades per day (`max_daily_trades = 2`)
- ✅ 4-hour cooldown between trades (`trade_cooldown_minutes = 240`)
- ✅ Max 2 concurrent positions (`max_positions = 2`)
- ✅ Signal filtering: Only executes on A+ setups with conviction
- ✅ No position in same symbol check (avoids overtrading)

**Verdict:** Excellent implementation of "trade less"

### 2. **Trade with Confidence** ✓ STRONG
- ✅ Conviction-based system (1-5 scale)
- ✅ Only trades on signals from `SignalGenerator` (requires explicit setup)
- ✅ AI logging to WEEX for transparency
- ✅ Multi-factor reasoning system (signal must have `reasons` list)
- ✅ Pre-trade validation (`can_trade()` checks)
- ✅ Won't trade if equity check fails

**Verdict:** Strong conviction framework

### 3. **Trade Big** ⚠️ MODERATE
Current sizing by conviction:
- Conviction 1-3: 2% risk, 3x leverage
- Conviction 4: 3% risk, 5x leverage  
- Conviction 5: 5% risk, 5x leverage

**Sizing Logic:**
```python
risk_capital = equity * risk_pct
notional_value = risk_capital / 0.02  # 2% stop distance
margin_required = notional_value / leverage
```

**For Conviction 5 @ $733 equity:**
- Risk: $36.65 (5%)
- Notional: $1,832.50
- Margin: $366.50
- Position: ~50% of equity

**Verdict:** Reasonable but conservative

---

## ⚠️ AREAS FOR IMPROVEMENT

### 1. Position Sizing - "Trade Bigger" on High Conviction
**Current Issue:**
- Max position uses only 50% equity check
- Conviction 5 trades are same leverage as Conviction 4
- Risk scales but leverage doesn't scale aggressively enough

**Recommendation:**
```python
# Suggested scaling for "Trade Big"
if conviction <= 2:
    risk_pct = 0.015  # 1.5% - low confidence
    leverage = 2
elif conviction == 3:
    risk_pct = 0.025  # 2.5%
    leverage = 3
elif conviction == 4:
    risk_pct = 0.04   # 4%
    leverage = 5
else:  # conviction == 5
    risk_pct = 0.06   # 6% - TRADE BIG
    leverage = 8      # Higher leverage for A+ setups
```

### 2. Partial Profit Taking Conflicts with "Trade Big"
**Current:**
- Takes 50% at TP1 (+3%)
- Remaining 50% at TP2 (+6%)

**Issue:**
- Early profit-taking reduces position size
- Conflicts with "let winners run" mentality
- A+ setups should stay bigger longer

**Recommendation:**
```python
# For Conviction 5 only - let it run
if conviction >= 5:
    take_profit_1 = None  # Skip TP1
    take_profit_2 = price * 1.10  # +10% full exit
else:
    # Keep partial taking for lower conviction
    take_profit_1 = price * 1.03
    take_profit_2 = price * 1.06
```

### 3. Stop Loss Too Tight for Leverage
**Current:**
- Fixed 2% stop distance for all trades
- At 5x leverage, this is -10% on equity
- At 8x leverage, would be -16% on equity

**Issue:**
- May get stopped out on noise
- Doesn't account for volatility

**Recommendation:**
- Use ATR-based stops
- Scale stop by conviction (tighter for higher conviction)
- Consider trailing stops for Conviction 5

### 4. Max Risk Per Trade Not Used
**Code shows:**
```python
self.max_risk_per_trade = 0.03  # 3% max risk
```

**But calculation uses conviction-based risk:**
```python
risk_pct = 0.02 to 0.05  # Can exceed max_risk_per_trade
```

**Issue:**
- `max_risk_per_trade` is defined but never enforced
- Conviction 5 can risk 5% (exceeds 3% max)

**Recommendation:**
```python
# Enforce cap
risk_pct = min(calculated_risk, self.max_risk_per_trade)
```

OR increase the cap:
```python
self.max_risk_per_trade = 0.06  # Allow 6% for A+ setups
```

---

## 📊 PHILOSOPHY ALIGNMENT SCORE

| Principle | Current | Target | Score |
|-----------|---------|--------|-------|
| Trade Less | 2/day, 4h cooldown | ≤3/day | 9/10 ✅ |
| Trade with Confidence | Conviction system + filtering | A+ only | 8/10 ✅ |
| Trade Big | 50% equity max | 60-80% on Conv 5 | 6/10 ⚠️ |

**Overall: 7.7/10** - Strong foundation, needs more aggression on high-conviction

---

## 🎯 RECOMMENDED CHANGES

### Priority 1: Scale Leverage with Conviction
```python
def calculate_position_size(self, signal: dict) -> dict:
    conviction = signal['conviction']
    equity = self.get_account_equity()
    price = signal['market_data']['price']

    # PHILOSOPHY: Trade BIG on high conviction
    if conviction <= 2:
        risk_pct = 0.015
        leverage = 2
    elif conviction == 3:
        risk_pct = 0.025
        leverage = 3
    elif conviction == 4:
        risk_pct = 0.04
        leverage = 6
    else:  # conviction >= 5 - A+ SETUP
        risk_pct = 0.06   # 6% risk = TRADE BIG
        leverage = 10     # Max aggression on best setups
    
    # ... rest of calculation
```

### Priority 2: Remove Partial Exits on Conviction 5
```python
# In calculate_position_size():
if conviction >= 5:
    # Let winners run - no partial taking
    take_profit_1 = None
    take_profit_2 = price * 1.12 if signal['side'] == 'LONG' else price * 0.88
else:
    # Keep partials for lower conviction
    take_profit_1 = price * 1.03 if signal['side'] == 'LONG' else price * 0.97
    take_profit_2 = price * 1.06 if signal['side'] == 'LONG' else price * 0.94
```

### Priority 3: Dynamic Stop Loss
```python
# Use 2x ATR or conviction-based
if conviction >= 5:
    stop_distance = 0.015  # Tighter stop for A+ setups
elif conviction >= 4:
    stop_distance = 0.02
else:
    stop_distance = 0.025  # Wider stop for lower conviction
```

### Priority 4: Increase Max Equity Allocation
```python
# Current check
if pos_calc['margin'] > equity * 0.5:
    return (False, f"Position too large...")

# Recommended for high conviction
max_margin_pct = 0.8 if signal['conviction'] >= 5 else 0.5
if pos_calc['margin'] > equity * max_margin_pct:
    return (False, f"Position too large...")
```

---

## 💭 PHILOSOPHY NOTES

The current implementation is **conservative and survivable** - good for consistent returns.

But for "Trade Big, Trade Less, Trade with Confidence":
- ✅ You're already trading less (great!)
- ✅ You have confidence filtering (great!)
- ⚠️ You're not trading big enough on A+ setups

**Key Insight:**
The whole point of "trade less" is to **wait for A+ setups, then GO BIG**. Current code identifies A+ setups (conviction 5) but doesn't fully capitalize on them.

**Conviction 5 should be:**
- 60-80% of equity deployed
- 8-10x leverage
- Wider targets (+10-15%)
- Let it run (no partial exits)

**Mental Model:**
- Conviction 1-3: "Maybe" → Small/skip
- Conviction 4: "Good setup" → Medium size
- **Conviction 5: "A+ SETUP" → FULL SEND** 🚀

---

## 🔄 SUGGESTED IMPLEMENTATION ORDER

1. **Week 1:** Increase leverage on Conv 5 (8x → 10x)
2. **Week 2:** Remove partial exits on Conv 5
3. **Week 3:** Dynamic stop loss by conviction
4. **Week 4:** Backtest and adjust risk percentages

---

## ⚖️ RISK CONSIDERATIONS

**Current (Safe):**
- Max loss per trade: 5% × 1 = 5%
- Max loss if 2 trades fail: 10%
- Recovery needed: +11%

**Proposed (Aggressive):**
- Max loss per trade: 6% × 1 = 6%
- Max loss if 2 trades fail: 12%
- Recovery needed: +14%

**Mitigation:**
- Keep max 2 trades/day limit
- Keep 4-hour cooldown
- Only use aggression on Conviction 5 (should be rare)
- Consider reducing to 1 position max for live testing

---

## 🎯 FINAL VERDICT

**Current Implementation: 7.7/10**

**Strengths:**
- Excellent "trade less" discipline
- Strong conviction framework
- Good risk management foundation
- AI logging transparency

**Weaknesses:**
- Not trading big enough on A+ setups
- Leverage doesn't scale with conviction
- Partial exits reduce position impact
- Conservative for competition environment

**Recommendation:**
The bot is built for **capital preservation**, but the competition requires **capital appreciation**. You need a "competition mode" that:
1. Increases leverage on Conv 5 (10x)
2. Increases risk on Conv 5 (6%)
3. Removes partial exits on Conv 5
4. Deploys 60-80% equity on A+ setups

**Trade Big, Trade Less, Trade with Confidence** = Wait patiently, then strike hard when you see it.

Current code: ✓ Waits patiently, ⚠️ strikes medium-hard

---
**End of Review**
