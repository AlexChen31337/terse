# AlphaStrike v2.0 Simulation Plan

**Date:** 2026-02-01  
**Status:** Ready to start  
**Duration:** 1 week minimum

---

## 🎯 Objective

Test v2.0 (20x leverage) in **simulation mode** before deploying to live trading.

**Why simulate first:**
- v2.0 is 4x more aggressive (20x vs 5x leverage)
- Tighter stops may reduce win rate
- +12% targets may take longer to hit
- Need to verify risk/reward in real market conditions

---

## 🔧 Setup

### Current Configuration

**v1.0 (LIVE)** - Running since 09:49
- Process ID: 1346463
- File: `run_live.sh`
- State: `state.json`
- Leverage: 5x max (Conv 5)
- Logs: `logs/alphastrike_YYYYMMDD.log`

**v2.0 (SIMULATION)** - Ready to start
- Script: `run_simulation_v2.sh`
- State: `state.json` (simulation mode = separate tracking)
- Leverage: 20x max (Conv 5)
- Logs: `logs/simulation_v2_YYYYMMDD.log`

### Comparison Tool

```bash
cd alphastrike
python3 compare_v1_v2.py
```

Shows side-by-side:
- Equity & P&L
- Win rate & avg win/loss
- Recent trades
- Open positions

---

## 📊 What We're Testing

### 1. Signal Quality with Tighter Stops

**v1.0:**
- Conv 5: 2.0% stop

**v2.0:**
- Conv 5: 1.5% stop (tighter)
- Conv 4: 2.0% stop
- Conv 3: 2.0% stop

**Question:** Do tighter stops on Conv 5 reduce win rate significantly?

### 2. Target Hit Rates

**v1.0:**
- TP1: +3% (take 50%)
- TP2: +6% (take 50%)

**v2.0 Conv 5:**
- TP: +12% (full exit, no partials)

**Question:** How often does price hit +12% vs +3%/+6%?

### 3. Position Sizing Impact

**v1.0 Conv 5:**
- 5x leverage
- ~50% equity allocation
- Example: $366 margin on $733 equity

**v2.0 Conv 5:**
- 20x leverage
- 80% equity allocation allowed
- Example: $586 margin potential (but risk-based sizing may use less)

**Question:** Is the added risk justified by added returns?

### 4. Conviction Distribution

**Question:** How many Conv 5 vs Conv 4 vs Conv 3 signals appear?
- If mostly Conv 3-4 → v2.0 won't differ much
- If mostly Conv 5 → v2.0 should significantly outperform

---

## 📈 Success Criteria

### After 1 Week Simulation:

**PASS if:**
- ✅ v2.0 P&L > v1.0 P&L by 20%+
- ✅ Win rate ≥ 50% on Conv 5 trades
- ✅ +12% target hit at least 40% of the time
- ✅ Max drawdown < 15%
- ✅ At least 5 Conv 5 signals generated

**CONSIDER if:**
- ⚠️ v2.0 P&L > v1.0 but by <20%
- ⚠️ Win rate 40-50% (acceptable but marginal)
- ⚠️ Drawdown 10-15%

**FAIL if:**
- ❌ v2.0 P&L < v1.0 P&L
- ❌ Win rate < 40%
- ❌ Max drawdown > 15%
- ❌ Stop loss hit rate > 60%

---

## 🎬 Running the Simulation

### Start v2.0 Simulation

```bash
cd /home/peter/clawd/alphastrike
./run_simulation_v2.sh
```

**This will:**
- Run every 5 minutes (same as live bot)
- Use v2.0 leverage/risk scaling
- Log to `logs/simulation_v2_YYYYMMDD.log`
- Send Telegram notifications (if configured)
- Track state separately from live bot

### Monitor Progress

**Live comparison:**
```bash
watch -n 60 "cd /home/peter/clawd/alphastrike && python3 compare_v1_v2.py"
```

**Check logs:**
```bash
tail -f alphastrike/logs/simulation_v2_$(date +%Y%m%d).log
```

**Manual check:**
```bash
cd alphastrike
python3 compare_v1_v2.py
```

---

## 📋 Daily Checklist

### Every 24 Hours:

1. **Run comparison:**
   ```bash
   cd alphastrike && python3 compare_v1_v2.py
   ```

2. **Review trades:**
   - What signals were generated?
   - What conviction levels?
   - Which hit TP vs SL?

3. **Check logs:**
   ```bash
   grep "EXECUTING TRADE" logs/simulation_v2_*.log
   grep "CLOSING POSITION" logs/simulation_v2_*.log
   ```

4. **Update tracking spreadsheet** (optional):
   - Date
   - v1.0 P&L
   - v2.0 P&L
   - Trades count
   - Win rate

---

## 🚨 Early Stop Conditions

**STOP simulation and revert if:**

1. **v2.0 down >10% while v1.0 is positive**
   - Indicates v2.0 over-leveraged or poor stop placement

2. **Stop loss hit 5+ times with 0 TP hits**
   - Stops too tight or signal quality poor

3. **No signals after 3 days**
   - Signal criteria too strict
   - May need to adjust thresholds

---

## 📊 Week 1 Analysis Template

### Day 7 Review:

```
v1.0 (LIVE):
- Equity: $____
- P&L: $____ (___%)
- Trades: ___
- Win Rate: ___%
- Max Drawdown: ___%

v2.0 (SIMULATION):
- Equity: $____
- P&L: $____ (___%)
- Trades: ___
- Win Rate: ___%
- Max Drawdown: ___%

VERDICT: [ PASS / CONSIDER / FAIL ]

NEXT STEPS:
- [ ] Deploy v2.0 to live
- [ ] Continue simulation another week
- [ ] Adjust parameters and re-test
- [ ] Revert to v1.0
```

---

## 🔄 If Simulation Passes

### Deployment Plan:

1. **Stop live v1.0 bot**
   ```bash
   pkill -f "python3 alphastrike.py --live"
   ```

2. **Backup v1.0 state**
   ```bash
   cp alphastrike/state.json alphastrike/state_v1_backup.json
   ```

3. **Start v2.0 live**
   ```bash
   cd alphastrike
   ./run_live.sh  # (update script to use new code)
   ```

4. **Monitor first 24 hours closely**
   - Check every 2-4 hours
   - Be ready to revert if needed

---

## 🔙 Rollback Plan

If v2.0 underperforms:

### Option 1: Partial Revert (Keep some improvements)
```python
# In calculate_position_size():
if conviction <= 2:
    risk_pct = 0.015
    leverage = 2
elif conviction == 3:
    risk_pct = 0.025
    leverage = 5
elif conviction == 4:
    risk_pct = 0.04
    leverage = 8    # Reduced from 10x
else:  # conviction >= 5
    risk_pct = 0.05  # Back to 5%
    leverage = 10    # Reduced from 20x
    stop_distance = 0.02  # Back to 2%
```

### Option 2: Full Revert to v1.0
```bash
git checkout alphastrike/alphastrike.py  # If using git
# Or restore from backup
```

---

## 🎯 Current Status

- ✅ v1.0 running live (PID 1346463)
- ✅ v2.0 code ready
- ✅ Simulation script ready
- ⏳ **Ready to start simulation**

**To start:**
```bash
cd /home/peter/clawd/alphastrike
./run_simulation_v2.sh
```

---
**End of Simulation Plan**
