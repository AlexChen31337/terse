# simmer-risk — Prediction Market Risk Management Framework

> **MANDATORY**: No real-money Simmer/Polymarket trade should be placed without passing `risk_check.py` first.

## Overview

Protects Bowen's real USDC on Simmer/Polymarket prediction markets. Built after fear-harvester ran uncontrolled BTC 5-min binary bets with no risk controls (−$90 SIM, trust loss).

**Scope:**
- ✅ **Real money** (Polymarket USDC) — full risk controls
- 📊 **$SIM virtual** — monitored, logged, but not auto-sold by default

---

## Files

```
simmer-risk/
├── monitor.py          # Position monitor (cron, hourly)
├── risk_check.py       # Pre-trade risk gate (call before every trade)
├── daily_report.py     # Daily P&L summary (cron, 9AM AEDT)
├── risk_config.json    # Risk parameters (edit to adjust thresholds)
├── test_monitor.py     # Tests (must pass before deploying changes)
├── README.md           # This file
└── data/
    ├── monitor_log.jsonl      # All monitor actions (append-only)
    ├── risk_check_log.jsonl   # All pre-trade checks (append-only)
    └── trading_paused.flag    # Created by circuit breaker (delete to resume)
```

---

## Quick Start

```bash
# Run position monitor (dry run — no trades)
uv run python skills/simmer-risk/monitor.py --dry-run

# Run position monitor (live — will trade if thresholds breached)
uv run python skills/simmer-risk/monitor.py

# Pre-trade risk check
uv run python skills/simmer-risk/risk_check.py \
    --market-id "59a30946-..." \
    --amount 5.0 \
    --venue polymarket

# Daily report
uv run python skills/simmer-risk/daily_report.py

# Run tests
uv run python skills/simmer-risk/test_monitor.py
```

---

## Risk Rules

### 1. Soft Stop-Loss (`stop_loss_pct: -0.20`)

If any position's unrealized PnL drops below **−20%** from entry cost:
- **Auto-sell entire position** via Simmer API
- Log to `monitor_log.jsonl`
- Alert to stdout (captured by cron email)

**Example**: Bought $10 of YES shares → position worth $7 → sell all.

### 2. Portfolio Circuit Breaker (`circuit_breaker_pct: -0.15`)

If total USDC portfolio (cash + exposure) drops **>15% below high-water mark**:
- **Pause ALL trading** (writes `data/trading_paused.flag`)
- Sets `trading_paused: true` in `risk_config.json`
- Every subsequent trade blocked by `risk_check.py` until manually reset

**High-water mark** starts at $18.00 (initial fund) and auto-updates when portfolio rises.

**To resume trading after circuit breaker:**
1. Review what caused the loss
2. Delete `data/trading_paused.flag`
3. Set `trading_paused: false` in `risk_config.json`
4. Run `monitor.py --dry-run` to verify clean state

### 3. Profit Taking (`take_profit_pct: 0.50`)

If any position's unrealized PnL exceeds **+50%** from entry:
- **Auto-sell half** the position
- Locks in gains, keeps exposure to upside

### 4. Position Size Limit (`max_position_pct: 0.30`)

Pre-trade check: no single trade can exceed **30% of total portfolio value**.
- Checked before every trade via `risk_check.py`
- Also blocks if trade would push total exposure over 90% of portfolio

### 5. Position Count Limit (`max_positions: 5`)

Pre-trade check: max **5 open real-money positions** at any time.
- $SIM virtual positions don't count toward this limit

---

## Pre-Trade Integration

**MANDATORY**: Every trading bot must call `risk_check.py` before placing a trade:

### Shell integration

```bash
# Run risk check
RESULT=$(uv run python skills/simmer-risk/risk_check.py \
    --market-id "$MARKET_ID" \
    --amount "$AMOUNT" \
    --venue polymarket \
    --caller "my-strategy")

APPROVED=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['approved'])")

if [ "$APPROVED" != "True" ]; then
    REASON=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['reason'])")
    echo "❌ Trade blocked: $REASON"
    exit 1
fi

# Proceed with trade
```

### Python integration

```python
import subprocess
import json

def check_before_trade(market_id: str, amount: float, venue: str = "polymarket") -> bool:
    result = subprocess.run(
        ["uv", "run", "python", "skills/simmer-risk/risk_check.py",
         "--market-id", market_id, "--amount", str(amount), "--venue", venue],
        capture_output=True, text=True, cwd="/home/bowen/clawd"
    )
    data = json.loads(result.stdout)
    if not data["approved"]:
        raise RuntimeError(f"Trade blocked: {data['reason']}")
    return True

# Or import directly:
import sys
sys.path.insert(0, "/home/bowen/clawd/skills/simmer-risk")
from risk_check import check_trade

result = check_trade(market_id="UUID", amount=5.0, venue="polymarket", caller="my-bot")
if not result["approved"]:
    raise RuntimeError(f"Trade denied: {result['reason']}")
```

---

## Cron Setup

### Install the cron jobs

Run these commands to add cron jobs:

```bash
# Edit crontab
crontab -e
```

Add these lines:

```cron
# Simmer position monitor — every hour
0 * * * * cd /home/bowen/clawd && uv run python skills/simmer-risk/monitor.py >> /home/bowen/clawd/skills/simmer-risk/data/cron_monitor.log 2>&1

# Simmer daily P&L report — 9 AM AEDT (UTC+11 in summer, UTC+10 in winter)
# 9 AM AEDT = 10 PM UTC previous day (summer)
0 22 * * * cd /home/bowen/clawd && uv run python skills/simmer-risk/daily_report.py 2>&1
```

**Note**: Adjust UTC offset for AEST/AEDT:
- AEDT (Oct–Apr): UTC+11, so 9 AM AEDT = 22:00 UTC previous day
- AEST (Apr–Oct): UTC+10, so 9 AM AEST = 23:00 UTC previous day

### Verify cron is working

```bash
# Check last monitor run
tail -20 /home/bowen/clawd/skills/simmer-risk/data/cron_monitor.log

# Check monitor log for recent events
tail -10 /home/bowen/clawd/skills/simmer-risk/data/monitor_log.jsonl | python3 -m json.tool
```

---

## Adjusting Risk Parameters

Edit `risk_config.json` directly. Changes take effect on next monitor run.

```json
{
  "stop_loss_pct": -0.20,         // -20%: sell if position drops this much
  "circuit_breaker_pct": -0.15,   // -15%: pause all trading if portfolio drops this much
  "take_profit_pct": 0.50,        // +50%: sell half when position up this much
  "max_position_pct": 0.30,       // 30%: max single trade vs portfolio
  "max_positions": 5,             // hard cap on open real-money positions
  "trading_paused": false,        // set true to pause all trades manually
  "high_water_mark": 18.00        // auto-updated, reflects best portfolio value seen
}
```

**To tighten risk (more conservative):**
- Decrease `stop_loss_pct` (e.g., `-0.10` for 10% stop-loss)
- Decrease `circuit_breaker_pct` (e.g., `-0.10`)
- Decrease `max_position_pct` (e.g., `0.20`)

**To loosen risk (more aggressive — not recommended):**
- Increase `stop_loss_pct` toward 0 (e.g., `-0.30`)

---

## Monitoring & Logs

### Monitor log format (`data/monitor_log.jsonl`)

One JSON object per line. Event types:
- `monitor_start` — monitor run began
- `circuit_breaker_check` — drawdown check result
- `circuit_breaker_triggered` — trading paused!
- `hwm_updated` — new portfolio high set
- `position_ok` — position within risk limits
- `position_skip` — position skipped (resolved/no shares/sim)
- `stop_loss_triggered` — position sold (stop-loss)
- `take_profit_triggered` — half position sold (profit-taking)
- `trade_attempt` — trade was submitted
- `monitor_complete` — run finished

### Risk check log format (`data/risk_check_log.jsonl`)

- `risk_check_approved` — trade passed all checks
- `risk_check_approved_sim` — $SIM trade approved (skips real checks)
- `risk_check_denied` — trade blocked, with `failed_at_check` field
- `risk_check_error` — couldn't fetch API data

---

## Running Tests

```bash
cd /home/bowen/clawd
uv run python skills/simmer-risk/test_monitor.py -v
```

Tests use temporary directories — no API calls, no config mutations. Run before any framework changes.

---

## Architecture

```
Any trading bot (fear-harvester, ai-domain-edge, etc.)
         │
         ▼
   risk_check.py ──► [approved?] ──NO──► LOG + EXIT
         │YES
         ▼
   Simmer API (POST /trade)
         │
         ▼
   monitor.py (runs hourly via cron)
         ├── check_circuit_breaker()  ← portfolio-level guard
         └── check_position()        ← per-position stop-loss / take-profit
                  └── simmer_trade() ← auto-sell if threshold crossed
```

---

## Emergency Procedures

### 🚨 Stop all trading NOW

```bash
# Method 1: Set flag file
echo '{"paused_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'", "reason": "Manual emergency stop"}' \
    > /home/bowen/clawd/skills/simmer-risk/data/trading_paused.flag

# Method 2: Edit config
python3 -c "
import json
from pathlib import Path
cfg = json.loads(Path('/home/bowen/clawd/skills/simmer-risk/risk_config.json').read_text())
cfg['trading_paused'] = True
Path('/home/bowen/clawd/skills/simmer-risk/risk_config.json').write_text(json.dumps(cfg, indent=2))
print('Trading paused.')
"
```

### Resume trading after pause

```bash
# Remove flag file
rm -f /home/bowen/clawd/skills/simmer-risk/data/trading_paused.flag

# Update config
python3 -c "
import json
from pathlib import Path
cfg = json.loads(Path('/home/bowen/clawd/skills/simmer-risk/risk_config.json').read_text())
cfg['trading_paused'] = False
Path('/home/bowen/clawd/skills/simmer-risk/risk_config.json').write_text(json.dumps(cfg, indent=2))
print('Trading resumed.')
"

# Verify clean state
uv run python skills/simmer-risk/monitor.py --dry-run
```
