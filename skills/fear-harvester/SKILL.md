# FearHarvester Skill

Autonomous DCA agent for extreme fear markets, targeting Hyperliquid spot (UBTC/USDC).

## Strategy

- Monitor Fear & Greed index continuously
- When F&G ≤ 20 (Extreme Fear): DCA into UBTC via Hyperliquid spot
- Hold for 120 days minimum (Sharpe 2.01 backtested)
- When F&G ≥ 50 (Neutral/Greed recovery) + past hold period: rebalance back to USDC
- Removes human emotion from "buy the fear"

## Exchange: Hyperliquid Spot

Target pair: UBTC/USDC (@142)
Mode: spot (holds real UBTC, not perp — no funding, no liquidation)

### Setup

```bash
export HL_PRIVATE_KEY="0x..."
export HL_WALLET_ADDRESS="0x..."
```

Or create `/home/bowen/.openclaw/skills/hyperliquid/.env`:
```
HL_PRIVATE_KEY=0x...
HL_WALLET_ADDRESS=0x...
```

### Execute

```bash
uv run python scripts/executor.py --dry-run          # simulate (no state, no API)
uv run python scripts/executor.py --paper             # local tracking (no API)
uv run python scripts/executor.py --live              # real trades on HL spot
uv run python scripts/executor.py --status            # show positions + P&L
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--buy-threshold` | 20 | F&G value to trigger DCA buy |
| `--sell-threshold` | 50 | F&G value to trigger rebalance |
| `--hold-days` | 120 | Minimum hold period before rebalance |
| `--dca-amount` | 500 | USD per DCA buy |
| `--max-capital` | 5000 | Maximum total capital deployed |
| `--testnet` | false | Use HL testnet |

### Modes

- **dry-run**: Simulates decisions, prints output. No state changes, no API calls.
- **paper**: Tracks positions in local `executor_state.json`. No exchange API calls.
- **live**: Places real IOC limit orders on Hyperliquid spot. Updates local state on fill.

## Usage

```bash
# Backtest historical performance
uv run python scripts/backtest.py --start 2018-01-01 --capital 10000

# Check current F&G signal
uv run python scripts/signals.py

# Run executor
uv run python scripts/executor.py --dry-run
```

## Historical Edge (2018-2024)

Buying F&G ≤ 20, holding 120d → Sharpe ratio 2.01
Buying F&G < 10, holding 90d → 40-80% average return

## Architecture

```
scripts/
  executor.py    — DCA execution engine (dry-run/paper/live via HL spot)
  signals.py     — Live F&G signal monitor
  backtest.py    — Historical backtesting
data/
  executor_state.json — Position tracking (paper/live)
tests/
  test_executor_hl.py — Executor tests (≥90% coverage)
```

## Dependencies

- `requests` — F&G API, Binance price feed
- Hyperliquid client (from `~/.openclaw/skills/hyperliquid/scripts/client.py`) — spot order execution
