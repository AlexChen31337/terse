# AlphaStrike v2.0 - "Trade Big" Upgrade

**Date:** 2026-02-01  
**Philosophy:** Trade Big, Trade Less, Trade with Confidence  
**Max Leverage:** 20x (on Conviction 5)

---

## 🚀 What Changed

### 1. Conviction-Based Leverage Scaling
**Old (v1.0):**
```python
Conv 1-3: 2% risk, 3x leverage
Conv 4:   3% risk, 5x leverage
Conv 5:   5% risk, 5x leverage  ← TOO CONSERVATIVE
```

**New (v2.0):**
```python
Conv 1-2: 1.5% risk, 2x leverage, 2.5% stop
Conv 3:   2.5% risk, 5x leverage, 2.0% stop
Conv 4:   4.0% risk, 10x leverage, 2.0% stop
Conv 5:   6.0% risk, 20x leverage, 1.5% stop  ← FULL SEND 🚀
```

**Impact:**
- Conviction 5 now uses **4x more leverage** (20x vs 5x)
- **20% more risk** on A+ setups (6% vs 5%)
- **Tighter stop** for high conviction (1.5% vs 2%)

---

### 2. Dynamic Position Size Limits
**Old:**
- Fixed 50% equity cap on all trades

**New:**
- Conv 5: 80% equity allocation (TRADE BIG)
- Conv 4: 60% equity allocation
- Conv 1-3: 40% equity allocation

**Example @ $733 equity:**
| Conviction | Old Max | New Max | Change |
|------------|---------|---------|--------|
| Conv 3 | $366 | $293 | -20% (safer) |
| Conv 4 | $366 | $440 | +20% |
| Conv 5 | $366 | $586 | **+60%** 🚀 |

---

### 3. Conviction 5: Let Winners Run
**Old:**
- Take 50% profit at +3%
- Take remaining 50% at +6%
- Max gain: 4.5% average

**New (Conv 5 only):**
- **NO partial exits**
- Single exit at +12%
- Let A+ setups run to bigger targets

**Why:**
The whole point of "Trade Big" is to **CAPITALIZE** on A+ setups. Taking partials at +3% defeats the purpose.

Conv 1-4 still use partials (3% / 6%) as before.

---

### 4. Tighter Stops on High Conviction
**Philosophy:** If you're convinced, set a tight stop. If it's questionable, give it room.

| Conviction | Stop Distance | Rationale |
|------------|---------------|-----------|
| 1-2 | 2.5% | Low confidence → wider stop |
| 3-4 | 2.0% | Standard stop |
| 5 | **1.5%** | High confidence → tight stop |

---

## 📊 Example Trades

### Conviction 5: BTC @ $78,485
**v1.0 (Conservative):**
- Risk: 5% = $36.65
- Leverage: 5x
- Notional: $1,832.50
- Margin: $366.50 (50% equity)
- Stop: -2% → -$36.65 loss
- TP1: +3% → Take 50%
- TP2: +6% → Take 50%
- **Max Gain: ~$82** (4.5% blended)

**v2.0 (FULL SEND):**
- Risk: 6% = $43.98
- Leverage: **20x**
- Notional: **$5,864**
- Margin: **$293.20** (40% equity used, but 80% allowed)
- Stop: -1.5% → -$43.98 loss
- TP: **+12%** → **$704** gain 🚀
- **ROI on equity: +96%** if TP hits

**Difference:** **8.6x more profit** on same setup!

---

### Conviction 4: ETH @ $2,500
**v1.0:**
- 3% risk, 5x leverage
- Margin: $366
- Notional: $1,830
- Max gain: ~$82

**v2.0:**
- **4% risk, 10x leverage**
- Margin: **$440** (60% cap)
- Notional: **$4,400**
- Max gain: +6% → **$264**

**Difference:** 3.2x more profit

---

## ⚖️ Risk Analysis

### Max Drawdown Scenarios

**v1.0 (2 losing trades):**
- Loss 1: 5% = $36.65
- Loss 2: 5% = $36.65
- Total: -$73.30 (-10%)
- Recovery needed: +11.1%

**v2.0 (2 Conv 5 losing trades):**
- Loss 1: 6% = $43.98
- Loss 2: 6% = $43.98
- Total: -$87.96 (-12%)
- Recovery needed: +13.6%

**Additional risk: 2% more drawdown**

**Mitigation:**
- Conviction 5 should be **rare** (only A+ setups)
- 4-hour cooldown prevents rapid losses
- Max 2 positions limits exposure
- Tight 1.5% stop on Conv 5 reduces slippage risk

---

## 🎯 Expected Performance Impact

### Assumptions:
- Conv 5 signals: 1-2 per week
- Win rate: 60% (slightly lower due to tighter stops)
- Avg hold time: 12-48 hours

### Monthly Projection (4 Conv 5 trades):
**v1.0:**
- 2.4 winners × $82 = $196.80
- 1.6 losers × -$36.65 = -$58.64
- **Net: +$138.16 (+18.8%)**

**v2.0:**
- 2.4 winners × $704 = $1,689.60
- 1.6 losers × -$43.98 = -$70.37
- **Net: +$1,619.23 (+220%!)** 🚀

**Caveat:** This assumes same win rate with tighter stops and bigger size. Real performance may vary.

---

## 🚨 Important Notes

### 1. Only For Live Competition Mode
This aggressive scaling is designed for **competition environments** where:
- High returns needed in short timeframe
- You're willing to accept higher volatility
- Capital preservation is secondary to capital appreciation

For **long-term wealth building**, consider:
- Reducing Conv 5 leverage to 10-15x
- Keeping 4% risk cap
- Using 60% position limit

### 2. Signal Quality is CRITICAL
With 20x leverage, **signal quality matters more than ever**. The SignalGenerator must be:
- ✅ Well-tested
- ✅ Filtering for A+ setups only
- ✅ Multi-timeframe confirmed
- ✅ High conviction = high probability

**If your signals aren't reliable, DO NOT use v2.0.**

### 3. Exchange Limits
WEEX allows up to 125x leverage, but:
- Liquidation risk increases exponentially
- 20x is aggressive but manageable
- Consider your account size vs. notional limits

### 4. Psychological Factors
20x leverage means:
- +1% price move = +20% on your margin
- -1% price move = -20% on your margin
- Swings will be **intense**

Can you handle seeing:
- +$200 → -$100 → +$500 in 30 minutes?
- If not, reduce leverage or trade smaller.

---

## 📝 Testing Recommendations

### Phase 1: Simulation (1 week)
- Run v2.0 in simulation mode
- Compare to v1.0 paper trades
- Analyze:
  - Win rate change (tighter stops)
  - Drawdown patterns
  - TP hit rates (+12% vs +3%/+6%)

### Phase 2: Small Live Test (1 week)
- Reduce starting equity to $100-200
- Test with 1-2 real Conv 5 trades
- Validate:
  - Order execution at 20x
  - Stop loss triggers
  - Emotional response to volatility

### Phase 3: Full Deployment
- Scale to full equity if results are positive
- Monitor daily P&L closely
- Be ready to revert to v1.0 if needed

---

## 🔧 Rollback Plan

If v2.0 performs poorly, revert changes:

```python
# In calculate_position_size():
if conviction >= 5:
    risk_pct = 0.05     # Back to 5%
    leverage = 5        # Back to 5x
    stop_distance = 0.02  # Back to 2%
```

```python
# In can_trade():
max_margin_pct = 0.5  # Back to 50% for all
```

---

## 📊 Code Changes Summary

**Files Modified:**
- `alphastrike/alphastrike.py`

**Key Functions Updated:**
1. `calculate_position_size()` - Conviction-based scaling
2. `can_trade()` - Dynamic position limits
3. `manage_positions()` - Handle None TP1 for Conv 5
4. `execute_trade()` - Logging improvements

**Lines Changed:** ~80 lines
**New Philosophy Comments:** Added header with scaling table

---

## ✅ Validation Checklist

Before going live with v2.0:
- [ ] Simulation testing completed (1+ week)
- [ ] Win rate acceptable with tighter stops (≥55%)
- [ ] Signal quality confirmed (Conv 5 = true A+ setups)
- [ ] Emotional readiness for 20x volatility
- [ ] Rollback plan documented
- [ ] Small capital test successful
- [ ] Risk limits understood and accepted

---

## 🎯 Final Thoughts

**v2.0 implements true "Trade Big, Trade Less, Trade with Confidence":**
- ✅ Trade Less: 2/day, 4h cooldown
- ✅ Confidence: Conv 5 = A+ only
- ✅ **Trade Big: 20x leverage, 6% risk, 80% equity, +12% targets**

This is **not for everyone**. It's designed for:
- Competition environments
- High-quality signal generators
- Traders comfortable with volatility
- Short-term aggressive growth

**When in doubt, start conservative and scale up gradually.**

Good luck. Trade smart. 🚀

---
**End of Upgrade Documentation**
