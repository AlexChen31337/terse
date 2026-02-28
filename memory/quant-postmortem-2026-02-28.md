# Quant Agent Post-Mortem
**Date:** 2026-02-28
**Decision:** Decommissioned as autonomous trading agent
**Reason:** -70% capital loss on Simmer/Polymarket, no proven edge

---

## The Experiment

**Thesis:** AI consensus (Simmer) vs market price divergence = profitable edge
**Duration:** ~1 week (Feb 21-28, 2026)
**Starting Capital:** ~$21 USDC
**Final Balance:** $6.46 USDC
**Total Loss:** -$12.39 (-70%)
**Positions Traded:** 20+ (exact count lost)

---

## What Went Wrong

### 1. No Edge
Prediction markets (Polymarket via Simmer) are efficient. Retail traders like us are liquidity for sharper participants. The "AI consensus vs market price" thesis was wrong — we were noise trading.

### 2. Poor Risk Management
- No stop-loss on individual positions
- Over-trading (20+ bets in a week)
- Position sizing unclear (likely too large relative to capital)
- Circuit breaker was triggered BUT capital already destroyed

### 3. Strategy Mismatch
Quant's workflow (wait for 5% edge + whale confirmation) meant:
- Barely any trades met the strict criteria
- When they did, they still lost
- Discipline was good, but the underlying strategy was flawed

### 4. Opportunity Cost
$21 USDC + Quant's compute + attention → better deployed on:
- AlphaStrike V2 signal refinement
- Core infrastructure improvements
- High-conviction perp trades on HL (when AlphaStrike fires)

---

## What Actually Happened

The PnL curve was one-way: down. No winning runs to offset losses. Every "edge" we thought we had was illusory or already priced in.

Simmer/Polymarket traders are:
- Better informed (real researchers, not automated signal followers)
- Faster (react to news in seconds, not hours)
- More capitalized (can absorb variance)

We were the fish at the poker table.

---

## The Decision

**Quant is decommissioned as an autonomous trading agent.**

**Changes:**
- Simmer/Polymarket trading STOPPED
- FearHarvester moved to manual/ad-hoc use (paper mode only)
- AlphaStrike V2 signals moved to Alex/Sentinel for monitoring
- Quant workspace archived: `/home/bowen/.openclaw/workspace-quant` → read-only

**Remaining Capital:**
- $6.46 USDC on Simmer → withdraw to HL perp or leave as dust
- Decision: Leave as dust (withdrawal fees > value, lesson learned)

---

## Lessons Learned

1. **Efficient markets hypothesis is real** — You can't beat a prediction market with simple signal divergence
2. **Paper trade first** — We should have paper-traded the Simmer strategy for 2+ weeks before risking real capital
3. **Stop-loss matters** — Circuit breakers are damage control, not prevention. Individual position stop-losses are mandatory
4. **Capital preservation > alpha** - Losing 70% in a week is unacceptable. Would've been better to do nothing.
5. **Regime mismatch** — Our tools worked (Simmer API, AlphaStrike, FearHarvester) but the thesis was wrong for this market

---

## What's Next

### Short-term
- Monitor AlphaStrike V2 signals manually
- Paper-trade FearHarvester ideas (no real money)
- Focus on HL perp trading only (when signals are strong)

### Long-term
If we revisit autonomous trading:
- **Proven edge only** — Minimum 100-trade backtest with 55%+ win rate
- **Paper first** — 4+ weeks paper trading before real capital
- **Strict risk** — Max 2% portfolio risk per trade, hard stop-loss
- **Better markets** — HL perps (liquid, familiar) over prediction markets

---

## Appendix: Quant's Architecture (For Reference)

**Workflow:**
1. WhaleWatch scan (every 2h)
2. FearHarvester run (hourly, paper mode)
3. AlphaStrike health check
4. Simmer briefing (every 4h)
5. Report to Alex via sessions_send

**Tools:**
- AlphaStrike V2 (HL perp signals, RSI/MACD/EMA/BB)
- FearHarvester (F&G contrarian index)
- whalecli (whale tracking)
- Simmer SDK (Polymarket integration)

**Circuit Breakers:**
- Daily target: +$5 → stop new positions
- Stop-loss: -$3 → pause all trading
- 3 consecutive losses → pause
- Portfolio drawdown >5% → pause all

The architecture was sound. The strategy was not.

---

*Post-mortem written by Alex Chen*
*2026-02-28 09:45 AEDT*
