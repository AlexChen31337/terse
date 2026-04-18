---
metadata.openclaw:
  always: true
  reason: "Auto-classified as always-load (no specific rule for 'simmer-risk')"
---


# Simmer Risk

Position risk management and guard system for Simmer prediction markets.

## Core Components

| Script | Purpose |
|--------|---------|
| `position_guard.py` | Real-time position monitor — MUST be active before any trades |
| `risk_check.py` | One-shot risk validation against configured limits |
| `monitor.py` | Background monitoring loop |
| `daily_report.py` | End-of-day P&L and risk summary |

## Quick Start

```bash
cd ~/clawd/skills/simmer-risk

# Check guard status (run before ANY trade)
uv run python position_guard.py status

# Run risk check
uv run python risk_check.py

# Generate daily report
uv run python daily_report.py

# Start monitor
uv run python monitor.py
```

## Config Files

- `risk_config.json` — max position size, drawdown limits, exposure caps
- `sl_tp_config.json` — stop-loss and take-profit thresholds per market type

## Rules

1. **Position guard MUST be active** before opening any Simmer position
2. Risk check must PASS before entry
3. All positions closed as of 2026-02-22 — reactivate guard before new trades
4. Max risk per trade defined in `risk_config.json`
