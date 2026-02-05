# AlphaStrike - High-Conviction Crypto Futures Trading Bot

## Overview

AlphaStrike implements a conservative, high-conviction trading strategy for WEEX futures:

**"Trade Big, Trade Less, Trade with Confidence"**

### Key Features
- ✅ **Wait for A+ setups** - No FOMO, no scalp trades
- ✅ **Maximum 2 trades per day** - Quality over quantity
- ✅ **Strict risk management** - Max 5% risk per trade
- ✅ **Clear entry/exit rules** - Every trade has a thesis
- ✅ **Simulation mode** - Test before risking real capital

---

## Quick Start

### 1. Run Diagnostic (Analyze Current Positions)
```bash
cd /home/peter/clawd/alphastrike
export WEEX_API_KEY="your_key"
export WEEX_API_SECRET="your_secret"
export WEEX_PASSPHRASE="your_passphrase"
python3 diagnose.py
```

### 2. Run Bot in Simulation Mode
```bash
# Run once and exit
python3 alphastrike.py --once

# Run continuously (scans every 5 minutes)
python3 alphastrike.py

# Custom scan interval (e.g., 10 minutes)
python3 alphastrike.py --interval 10
```

### 3. Go Live (After Testing)
```bash
# WARNING: This trades real money!
python3 alphastrike.py --live
```

---

## Directory Structure

```
/home/peter/clawd/alphastrike/
├── STRATEGY.md          # Complete strategy documentation
├── README.md            # This file
├── alphastrike.py       # Main trading bot
├── signals.py           # Signal generator
├── market_data.py       # Market data fetcher & indicators
├── diagnose.py          # Position analysis tool
├── state.json           # Bot state (auto-created)
└── logs/                # Trade logs (auto-created)
    └── alphastrike_YYYYMMDD.log
```

---

## Current Situation Analysis

### What Went Wrong with Existing Positions

**Current Positions (All Underwater):**
- **ETH SHORT**: Entry $2412 → Current $2421 (-$0.56)
- **DOGE SHORT**: Entry $0.1023 → Current $0.1027 (-$0.54)
- **BNB SHORT**: Entry $774 → Current $778 (-$0.57)
- **Total Loss**: -$1.67 (on ~$213 margin)

**Root Causes Identified:**
1. ❌ **No Edge Detection** - No technical confirmation
2. ❌ **No Stop Loss** - No defined invalidation point
3. ❌ **Low Conviction** - Shorting strong assets in bull market
4. ❌ **Over-diversification** - 3 weak positions vs 1 strong position
5. ❌ **No Exit Plan** - No profit targets or trailing stops

**Why AlphaStrike Wouldn't Have Made These Trades:**

For a LONG signal, AlphaStrike requires:
- ✅ RSI < 30 (oversold) OR bouncing from oversold
- ✅ Price > EMA 20 AND EMA 9 > EMA 20 (uptrend)
- ✅ Volume spike confirmation
- ✅ Funding rate not extreme

For a SHORT signal, AlphaStrike requires:
- ✅ RSI > 70 (overbought) OR rejecting from overbought
- ✅ Price < EMA 20 AND EMA 9 < EMA 20 (downtrend)
- ✅ Volume spike
- ✅ **Funding rate > 0.05%** (extreme long bias)

**Current markets don't meet these criteria.**

---

## AlphaStrike Strategy Summary

### A+ Setup Criteria (Must Have 4/5 Required + 2 Bonus for Level 3)

#### LONG Setup (Bull Market Bias)
**Required:**
1. RSI < 30 OR RSI crossed from <30 to >35
2. Price > EMA 20 AND EMA 9 > EMA 20
3. Volume spike > 1.5x average
4. Funding rate neutral/positive (< 0.01%)

**Bonus:**
- Price bouncing from EMA 50 support
- 24h change between -3% to +3%
- Positive wick rejection on 15m/1h

#### SHORT Setup (Rare, High Conviction)
**Required:**
1. RSI > 70 OR RSI crossed from >70 to <65
2. Price < EMA 20 AND EMA 9 < EMA 20
3. Volume spike > 1.5x average
4. **Funding rate > 0.05%** (extreme)

**Bonus:**
- Price rejected from EMA 50 resistance
- 24h change > +10% (overextended)
- Multiple upper wick rejections

### Position Sizing

| Conviction | Risk | Leverage | Example (on $733 equity) |
|------------|------|----------|---------------------------|
| Level 1 (3/5) | 2% | 3x | $14 risk → $700 notional |
| Level 2 (4/5) | 3% | 5x | $22 risk → $1,100 notional |
| Level 3 (5/5+2) | 5% | 5-10x | $36 risk → $1,800 notional |

### Risk Management

**Per Trade:**
- Stop loss: 1.5-2% from entry
- TP1: 50% position at +3%
- TP2: 50% position at +6%
- Breakeven: When price moves +2%

**Account Level:**
- Max daily loss: 5% of equity → STOP TRADING
- Max drawdown: 15% from peak → REVIEW STRATEGY
- Max concurrent positions: 2
- Max trades per day: 2
- Cooldown between trades: 4 hours

---

## Trading Universe

Top 5 liquid pairs:
1. **BTC/USDT** - King liquidity
2. **ETH/USDT** - High correlation
3. **SOL/USDT** - Volatile
4. **BNB/USDT** - Stable
5. **DOGE/USDT** - Retail favorite

---

## Simulation Mode

Before trading real capital, run in simulation mode for **minimum 7 days**.

### Success Metrics
- ✅ Win rate > 60%
- ✅ Profit factor > 2.0
- ✅ Max drawdown < 10%
- ✅ 10+ trades executed

### Go-Live Checklist
- [ ] 7+ days simulation complete
- [ ] Win rate > 60%
- [ ] Profit factor > 2.0
- [ ] Max drawdown < 10%
- [ ] Edge consistent across market conditions
- [ ] All edge cases handled

---

## Expected Performance

### Conservative Goals
- **Monthly Return**: 10-20% (compounded)
- **Max Drawdown**: < 10%
- **Win Rate**: > 55%
- **Profit Factor**: > 1.8
- **Sharpe Ratio**: > 2.0

### Trade Frequency
- **Average**: 3-5 trades per week
- **Max**: 2 trades per day
- **Typical**: 0-2 signals per day

---

## Logs and Monitoring

### Log Files
- `logs/alphastrike_YYYYMMDD.log` - Daily logs
- `state.json` - Bot state (positions, equity, history)

### What Gets Logged
- Every signal with full rationale
- Every trade execution (entry, size, stops)
- Every position close (P&L, reason)
- Equity updates
- Error conditions

---

## Commands Reference

```bash
# Diagnose current positions
python3 diagnose.py

# Run bot once (scan and exit)
python3 alphastrike.py --once

# Run continuously (5-minute scans)
python3 alphastrike.py

# Custom interval (10 minutes)
python3 alphastrike.py --interval 10

# Go live (REAL MONEY)
python3 alphastrike.py --live

# Live with custom interval
python3 alphastrike.py --live --interval 15
```

---

## Important Notes

### ⚠️ Warnings
- **NEVER blow up the account** - Capital preservation is job #1
- **When in doubt, stay out** - Missing a trade is better than losing money
- **Don't chase** - If price moves >1% from signal, skip it
- **Respect the cooldown** - 4 hours minimum between trades

### ✅ Best Practices
- **Review logs daily** - Learn from every trade
- **Stick to the plan** - Don't override signals
- **Monitor drawdown** - Stop if >15% from peak
- **Document decisions** - Every trade needs a rationale

### 🚫 Red Flags
- Overtrading (more than 2/day)
- Moving stops against position
- Ignoring signals (FOMO or fear)
- Revenge trading after losses
- Trading during blackout periods

---

## Troubleshooting

### Bot not finding signals
- **Normal!** AlphaStrike waits for A+ setups
- May take days to find perfect conditions
- This is a feature, not a bug

### "Can't trade: Max positions reached"
- Close existing positions first
- Or wait for them to hit TP/SL

### "Can't trade: Cooldown active"
- Wait 4 hours between trades
- Forces patience and reflection

### API errors
- Check environment variables are set
- Verify API credentials are valid
- Check internet connection

---

## Next Steps

1. **Review STRATEGY.md** - Complete strategy details
2. **Run diagnose.py** - See what went wrong before
3. **Start simulation** - `python3 alphastrike.py --once`
4. **Monitor for 7 days** - Check logs, track performance
5. **Review and adjust** - Tweak parameters if needed
6. **Go live cautiously** - Start with 2% risk per trade
7. **Scale up slowly** - Increase size only after proving edge

---

## Philosophy

> **"Trade Big, Trade Less, Trade with Confidence"**

This isn't about maximizing trade frequency. It's about maximizing edge per trade.

One A+ setup with 5% risk and 6% target beats ten B- trades with 2% risk and 3% targets.

**Patience + Conviction + Risk Management = Profitability**

---

## Version

- **Version**: 1.0
- **Created**: 2025-01-31
- **Status**: Simulation testing phase

---

## Questions?

Review the full strategy in `STRATEGY.md` or check logs in `logs/alphastrike_YYYYMMDD.log`.
