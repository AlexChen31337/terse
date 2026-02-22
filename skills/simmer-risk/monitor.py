#!/usr/bin/env python3
"""
Simmer Risk Monitor — Position monitor for Simmer/Polymarket prediction market trading.

Runs via cron every hour. Applies:
  - Soft stop-loss:       sell entire position if PnL < -20% from entry
  - Portfolio circuit breaker: pause ALL trading if portfolio loss > -15% from HWM
  - Profit taking:        sell half position if PnL > +50% from entry

Focuses on REAL money (Polymarket USDC) positions.
$SIM virtual positions are monitored but not auto-sold (logged only).

Usage:
    uv run python monitor.py
    uv run python monitor.py --dry-run     # simulate only, no trades
    uv run python monitor.py --all-venues  # include $SIM positions
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SKILL_DIR = Path(__file__).parent
CONFIG_PATH = SKILL_DIR / "risk_config.json"
DATA_DIR = SKILL_DIR / "data"
LOG_PATH = DATA_DIR / "monitor_log.jsonl"
PAUSE_FLAG = DATA_DIR / "trading_paused.flag"
CREDS_PATH = Path.home() / ".config/simmer/credentials.json"

BASE_URL = "https://api.simmer.markets/api/sdk"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_creds() -> dict[str, Any]:
    return json.loads(CREDS_PATH.read_text())


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text())


def save_config(cfg: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(event: dict[str, Any]) -> None:
    """Append a JSON event to the monitor log."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    event["timestamp"] = now_iso()
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(event) + "\n")


def alert(msg: str) -> None:
    """Print alert to stdout (captured by cron/email)."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[SIMMER-RISK ALERT] {ts} | {msg}", flush=True)


def simmer_get(api_key: str, path: str, params: Optional[dict] = None) -> dict[str, Any]:
    """GET request to Simmer API."""
    resp = requests.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        headers={"Authorization": f"Bearer {api_key}"},
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def simmer_trade(
    api_key: str,
    market_id: str,
    side: str,
    shares: float,
    venue: str,
    reasoning: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute a SELL trade on Simmer API."""
    payload = {
        "market_id": market_id,
        "side": side,
        "shares": round(shares, 6),
        "action": "sell",
        "venue": venue,
        "order_type": "FAK",  # Fill And Kill — best for bots
        "reasoning": reasoning,
        "source": "sdk:simmer-risk-monitor",
    }

    log_event({
        "event": "trade_attempt",
        "dry_run": dry_run,
        "market_id": market_id,
        "side": side,
        "shares": shares,
        "venue": venue,
        "reasoning": reasoning,
    })

    if dry_run:
        return {"success": True, "dry_run": True, "payload": payload}

    resp = requests.post(
        f"{BASE_URL}/trade",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Risk calculations
# ---------------------------------------------------------------------------

def compute_pnl_pct(position: dict[str, Any]) -> Optional[float]:
    """
    Calculate PnL percentage from entry for a position.

    Returns None if cost_basis is 0 or undefined (can't compute).
    Uses pnl field from API if cost_basis is positive.
    """
    cost_basis = position.get("cost_basis", 0)
    pnl = position.get("pnl", 0)

    if cost_basis is None or cost_basis <= 0:
        # Can't compute meaningful pct if basis is zero or negative
        return None

    return pnl / cost_basis


def get_position_side(position: dict[str, Any]) -> Optional[str]:
    """Determine which side (yes/no) we hold shares in."""
    shares_yes = position.get("shares_yes", 0) or 0
    shares_no = position.get("shares_no", 0) or 0
    if shares_yes > 0:
        return "yes"
    if shares_no > 0:
        return "no"
    return None


def get_position_shares(position: dict[str, Any]) -> float:
    """Get total shares held in the winning side."""
    shares_yes = position.get("shares_yes", 0) or 0
    shares_no = position.get("shares_no", 0) or 0
    return max(shares_yes, shares_no)


# ---------------------------------------------------------------------------
# Core monitor logic
# ---------------------------------------------------------------------------

def check_circuit_breaker(
    portfolio: dict[str, Any],
    config: dict[str, Any],
    dry_run: bool = False,
) -> bool:
    """
    Check if total portfolio has dropped >15% from high-water mark.

    Returns True if circuit breaker was triggered (trading should pause).
    """
    # Only use USDC real money for circuit breaker
    balance_usdc = portfolio.get("balance_usdc", 0) or 0
    polymarket_pnl = portfolio.get("polymarket_pnl", 0) or 0
    pnl_total = portfolio.get("pnl_total", 0) or 0

    # Total real money portfolio value
    # balance_usdc (cash) + total_exposure (open positions at current value)
    total_exposure = portfolio.get("total_exposure", 0) or 0
    total_portfolio_value = balance_usdc + total_exposure

    hwm = config.get("high_water_mark", 18.0)
    cb_pct = config.get("circuit_breaker_pct", -0.15)

    if hwm <= 0:
        return False

    drawdown_pct = (total_portfolio_value - hwm) / hwm

    log_event({
        "event": "circuit_breaker_check",
        "total_portfolio_value": total_portfolio_value,
        "balance_usdc": balance_usdc,
        "total_exposure": total_exposure,
        "high_water_mark": hwm,
        "drawdown_pct": round(drawdown_pct, 4),
        "threshold": cb_pct,
        "triggered": drawdown_pct <= cb_pct,
    })

    if drawdown_pct <= cb_pct:
        trigger_msg = (
            f"🚨 CIRCUIT BREAKER TRIGGERED: portfolio ${total_portfolio_value:.2f} "
            f"vs HWM ${hwm:.2f} = {drawdown_pct*100:.1f}% drawdown "
            f"(threshold: {cb_pct*100:.0f}%)"
        )
        alert(trigger_msg)

        if not dry_run:
            # Write pause flag file
            PAUSE_FLAG.parent.mkdir(parents=True, exist_ok=True)
            PAUSE_FLAG.write_text(json.dumps({
                "paused_at": now_iso(),
                "reason": trigger_msg,
                "portfolio_value": total_portfolio_value,
                "high_water_mark": hwm,
                "drawdown_pct": drawdown_pct,
            }, indent=2))

            # Update config
            config["trading_paused"] = True
            save_config(config)

        log_event({
            "event": "circuit_breaker_triggered",
            "portfolio_value": total_portfolio_value,
            "high_water_mark": hwm,
            "drawdown_pct": drawdown_pct,
            "dry_run": dry_run,
        })
        return True

    # Update high-water mark if we've hit a new high
    if total_portfolio_value > hwm and not dry_run:
        old_hwm = hwm
        config["high_water_mark"] = round(total_portfolio_value, 4)
        save_config(config)
        log_event({
            "event": "hwm_updated",
            "old_hwm": old_hwm,
            "new_hwm": total_portfolio_value,
        })

    return False


def check_position(
    api_key: str,
    position: dict[str, Any],
    config: dict[str, Any],
    include_sim: bool = False,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """
    Apply risk rules to a single position.

    Returns list of actions taken.
    """
    actions: list[dict[str, Any]] = []

    market_id = position.get("market_id")
    question = position.get("question", "?")
    venue = position.get("venue", "simmer")
    currency = position.get("currency", "$SIM")
    current_value = position.get("current_value", 0) or 0
    cost_basis = position.get("cost_basis", 0) or 0

    # Determine position status:
    # - Simmer positions have explicit "status" field ("active" / "resolved")
    # - Polymarket positions have NO status field — treat as active if they have shares
    status = position.get("status")
    shares_yes = position.get("shares_yes", 0) or 0
    shares_no = position.get("shares_no", 0) or 0
    has_shares = (shares_yes + shares_no) > 0

    if status is not None and status != "active":
        # Explicitly not active (e.g., "resolved")
        return actions
    if status is None and not has_shares:
        # No status field AND no shares → skip
        return actions

    # Skip $SIM positions unless explicitly included
    is_real_money = venue == "polymarket" and currency == "USDC"
    if not is_real_money and not include_sim:
        return actions

    pnl_pct = compute_pnl_pct(position)
    side = get_position_side(position)
    shares = get_position_shares(position)

    if pnl_pct is None or side is None or shares <= 0:
        log_event({
            "event": "position_skip",
            "market_id": market_id,
            "reason": "Cannot compute pnl_pct or no shares",
            "cost_basis": cost_basis,
            "side": side,
            "shares": shares,
        })
        return actions

    stop_loss_pct = config.get("stop_loss_pct", -0.20)
    take_profit_pct = config.get("take_profit_pct", 0.50)

    venue_label = f"{venue}/{currency}"
    pnl_label = f"{pnl_pct*100:+.1f}%"

    # --- Stop-loss check ---
    if pnl_pct < stop_loss_pct:
        reason = (
            f"Stop-loss: position at {pnl_label} "
            f"(threshold: {stop_loss_pct*100:.0f}%) — selling all {shares:.4f} shares"
        )
        alert(f"🛑 STOP-LOSS | {venue_label} | {question[:60]} | {reason}")

        result = simmer_trade(
            api_key=api_key,
            market_id=market_id,
            side=side,
            shares=shares,
            venue=venue,
            reasoning=f"Risk manager: stop-loss at {pnl_label}. Cutting loss.",
            dry_run=dry_run,
        )

        action = {
            "event": "stop_loss_triggered",
            "market_id": market_id,
            "question": question,
            "venue": venue,
            "pnl_pct": pnl_pct,
            "shares_sold": shares,
            "side": side,
            "current_value": current_value,
            "cost_basis": cost_basis,
            "dry_run": dry_run,
            "trade_result": result,
        }
        log_event(action)
        actions.append(action)

    # --- Profit-taking check ---
    elif pnl_pct >= take_profit_pct:
        shares_to_sell = shares / 2.0  # Sell half
        reason = (
            f"Take-profit: position at {pnl_label} "
            f"(threshold: {take_profit_pct*100:.0f}%) — selling half ({shares_to_sell:.4f} shares)"
        )
        alert(f"💰 TAKE-PROFIT | {venue_label} | {question[:60]} | {reason}")

        result = simmer_trade(
            api_key=api_key,
            market_id=market_id,
            side=side,
            shares=shares_to_sell,
            venue=venue,
            reasoning=f"Risk manager: take-profit at {pnl_label}. Selling half.",
            dry_run=dry_run,
        )

        action = {
            "event": "take_profit_triggered",
            "market_id": market_id,
            "question": question,
            "venue": venue,
            "pnl_pct": pnl_pct,
            "shares_sold": shares_to_sell,
            "side": side,
            "current_value": current_value,
            "cost_basis": cost_basis,
            "dry_run": dry_run,
            "trade_result": result,
        }
        log_event(action)
        actions.append(action)

    else:
        # Position is within normal range — log for audit trail
        log_event({
            "event": "position_ok",
            "market_id": market_id,
            "question": question[:80],
            "venue": venue,
            "pnl_pct": round(pnl_pct, 4),
            "current_value": current_value,
            "cost_basis": cost_basis,
            "near_stop_loss": pnl_pct < (stop_loss_pct * 0.75),  # within 75% of stop-loss
        })

        # Warn if approaching stop-loss (within 75%)
        if pnl_pct < (stop_loss_pct * 0.75):
            alert(
                f"⚠️  APPROACHING STOP-LOSS | {venue_label} | {question[:60]} | "
                f"PnL: {pnl_label} (stop at {stop_loss_pct*100:.0f}%)"
            )

    return actions


def run_monitor(dry_run: bool = False, include_sim: bool = False) -> None:
    """Main monitor loop."""
    print(f"[{now_iso()}] Starting Simmer Risk Monitor (dry_run={dry_run})", flush=True)

    creds = load_creds()
    api_key = creds["api_key"]
    config = load_config()

    # Check if trading is already paused
    if config.get("trading_paused") or PAUSE_FLAG.exists():
        alert("⚠️  Trading is PAUSED (circuit breaker active). Monitor still running.")
        log_event({"event": "monitor_run_paused", "reason": "trading_paused flag set"})

    # --- Fetch portfolio ---
    try:
        portfolio = simmer_get(api_key, "/portfolio")
    except Exception as e:
        alert(f"❌ Failed to fetch portfolio: {e}")
        log_event({"event": "fetch_error", "endpoint": "portfolio", "error": str(e)})
        sys.exit(1)

    log_event({
        "event": "monitor_start",
        "portfolio": {
            "balance_usdc": portfolio.get("balance_usdc"),
            "total_exposure": portfolio.get("total_exposure"),
            "positions_count": portfolio.get("positions_count"),
            "pnl_total": portfolio.get("pnl_total"),
            "polymarket_pnl": portfolio.get("polymarket_pnl"),
        },
        "dry_run": dry_run,
    })

    # --- Circuit breaker check ---
    cb_triggered = check_circuit_breaker(portfolio, config, dry_run=dry_run)

    # --- Fetch positions ---
    try:
        pos_data = simmer_get(api_key, "/positions")
    except Exception as e:
        alert(f"❌ Failed to fetch positions: {e}")
        log_event({"event": "fetch_error", "endpoint": "positions", "error": str(e)})
        sys.exit(1)

    positions = pos_data.get("positions", [])
    active_positions = [p for p in positions if p.get("status") == "active"]

    print(
        f"  Portfolio: ${portfolio.get('balance_usdc', 0):.2f} USDC cash + "
        f"${portfolio.get('total_exposure', 0):.2f} exposure | "
        f"{len(active_positions)} active positions",
        flush=True,
    )

    # --- Check each position ---
    all_actions: list[dict[str, Any]] = []

    if cb_triggered:
        print("  Circuit breaker triggered — skipping individual position checks.", flush=True)
    else:
        for pos in active_positions:
            actions = check_position(
                api_key, pos, config,
                include_sim=include_sim,
                dry_run=dry_run,
            )
            all_actions.extend(actions)

    # --- Summary ---
    n_actions = len(all_actions)
    log_event({
        "event": "monitor_complete",
        "actions_taken": n_actions,
        "circuit_breaker": cb_triggered,
        "dry_run": dry_run,
    })

    if n_actions > 0:
        alert(f"✅ Monitor complete: {n_actions} action(s) taken.")
    else:
        print(f"  ✓ All positions within risk limits. No actions taken.", flush=True)

    print(f"[{now_iso()}] Monitor done. Actions: {n_actions}", flush=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Simmer Risk Monitor")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulate only — no actual trades or config changes",
    )
    parser.add_argument(
        "--all-venues", action="store_true",
        help="Include $SIM virtual positions (default: real money only)",
    )
    args = parser.parse_args()
    run_monitor(dry_run=args.dry_run, include_sim=args.all_venues)


if __name__ == "__main__":
    main()
