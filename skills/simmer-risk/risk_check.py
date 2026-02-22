#!/usr/bin/env python3
"""
Simmer Pre-Trade Risk Check — Call this before ANY trade.

Usage:
    uv run python risk_check.py --market-id UUID --amount 5.0 --venue polymarket
    uv run python risk_check.py --market-id UUID --amount 5.0 --venue polymarket --side yes

Returns JSON: {"approved": true/false, "reason": "..."}
Exit code: 0 = approved, 1 = denied.

Can also be imported:
    from risk_check import check_trade
    result = check_trade(market_id="UUID", amount=5.0, venue="polymarket")
    if not result["approved"]:
        raise RuntimeError(f"Trade denied: {result['reason']}")
"""
from __future__ import annotations

import argparse
import json
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
LOG_PATH = DATA_DIR / "risk_check_log.jsonl"
PAUSE_FLAG = DATA_DIR / "trading_paused.flag"
CREDS_PATH = Path.home() / ".config/simmer/credentials.json"

BASE_URL = "https://api.simmer.markets/api/sdk"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text())


def load_creds() -> dict[str, Any]:
    return json.loads(CREDS_PATH.read_text())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_check(event: dict[str, Any]) -> None:
    """Append risk check event to log."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    event["timestamp"] = now_iso()
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(event) + "\n")


def deny(reason: str, details: Optional[dict] = None) -> dict[str, Any]:
    result: dict[str, Any] = {"approved": False, "reason": reason}
    if details:
        result.update(details)
    return result


def approve(reason: str = "All risk checks passed", details: Optional[dict] = None) -> dict[str, Any]:
    result: dict[str, Any] = {"approved": True, "reason": reason}
    if details:
        result.update(details)
    return result


def simmer_get(api_key: str, path: str) -> dict[str, Any]:
    resp = requests.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_trading_paused(config: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Check 1: Is trading paused by circuit breaker?"""
    if config.get("trading_paused", False):
        return deny(
            "Trading is PAUSED — circuit breaker active. "
            "Resolve by manually resetting trading_paused=false in risk_config.json "
            "after reviewing portfolio losses."
        )
    if PAUSE_FLAG.exists():
        try:
            flag_data = json.loads(PAUSE_FLAG.read_text())
            reason = flag_data.get("reason", "circuit breaker")
            return deny(f"Trading is PAUSED (flag file): {reason}")
        except Exception:
            return deny("Trading is PAUSED (flag file exists)")
    return None


def check_position_count(
    positions: list[dict[str, Any]],
    config: dict[str, Any],
    venue: str,
) -> Optional[dict[str, Any]]:
    """Check 2: Too many open positions?"""
    max_pos = config.get("max_positions", 5)

    # Count only real money active positions for real money trades
    # Note: Polymarket positions may not have a "status" field — treat as active if they have shares
    if venue == "polymarket":
        def _is_active(p: dict) -> bool:
            status = p.get("status")
            if status is not None:
                return status == "active"
            shares = (p.get("shares_yes") or 0) + (p.get("shares_no") or 0)
            return shares > 0

        open_real = [
            p for p in positions
            if _is_active(p)
            and p.get("venue") == "polymarket"
            and p.get("currency") == "USDC"
        ]
        count = len(open_real)
        if count >= max_pos:
            return deny(
                f"Position limit reached: {count}/{max_pos} open real-money positions. "
                "Close existing positions before opening new ones.",
                details={"open_positions": count, "max_positions": max_pos},
            )
    return None


def check_position_size(
    amount: float,
    portfolio: dict[str, Any],
    config: dict[str, Any],
    venue: str,
) -> Optional[dict[str, Any]]:
    """Check 3: Is position size within max_position_pct of portfolio?"""
    max_pct = config.get("max_position_pct", 0.30)

    if venue == "polymarket":
        balance_usdc = portfolio.get("balance_usdc", 0) or 0
        total_exposure = portfolio.get("total_exposure", 0) or 0
        portfolio_value = balance_usdc + total_exposure

        if portfolio_value <= 0:
            return deny("Cannot check position size: portfolio value is 0 or unknown")

        position_pct = amount / portfolio_value
        max_amount = portfolio_value * max_pct

        if position_pct > max_pct:
            return deny(
                f"Position size ${amount:.2f} exceeds {max_pct*100:.0f}% of portfolio "
                f"(${portfolio_value:.2f}). Max allowed: ${max_amount:.2f}.",
                details={
                    "amount": amount,
                    "portfolio_value": portfolio_value,
                    "position_pct": round(position_pct, 4),
                    "max_position_pct": max_pct,
                    "max_allowed_amount": round(max_amount, 2),
                },
            )
    return None


def check_portfolio_exposure(
    amount: float,
    portfolio: dict[str, Any],
    config: dict[str, Any],
    venue: str,
) -> Optional[dict[str, Any]]:
    """Check 4: Does this trade push exposure too high?"""
    if venue != "polymarket":
        return None  # Only check for real money

    balance_usdc = portfolio.get("balance_usdc", 0) or 0
    total_exposure = portfolio.get("total_exposure", 0) or 0
    portfolio_value = balance_usdc + total_exposure

    # After trade, new exposure
    new_exposure = total_exposure + amount
    new_exposure_pct = new_exposure / portfolio_value if portfolio_value > 0 else 1.0

    # Don't allow exposure > 90% of portfolio (keep 10% cash buffer)
    max_exposure_pct = 0.90
    if new_exposure_pct > max_exposure_pct:
        return deny(
            f"Trade would push exposure to {new_exposure_pct*100:.1f}% of portfolio "
            f"(max: {max_exposure_pct*100:.0f}%). "
            f"Insufficient USDC cash buffer. Available: ${balance_usdc:.2f}.",
            details={
                "current_exposure": total_exposure,
                "new_exposure": new_exposure,
                "portfolio_value": portfolio_value,
                "new_exposure_pct": round(new_exposure_pct, 4),
                "balance_usdc": balance_usdc,
            },
        )

    return None


def check_circuit_breaker_proximity(
    portfolio: dict[str, Any],
    config: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """Check 5: Are we near the circuit breaker threshold?"""
    hwm = config.get("high_water_mark", 18.0)
    cb_pct = config.get("circuit_breaker_pct", -0.15)

    balance_usdc = portfolio.get("balance_usdc", 0) or 0
    total_exposure = portfolio.get("total_exposure", 0) or 0
    portfolio_value = balance_usdc + total_exposure

    if hwm <= 0:
        return None

    drawdown_pct = (portfolio_value - hwm) / hwm

    # If we're within 50% of the circuit breaker threshold, warn but don't deny
    warning_threshold = cb_pct * 0.5  # e.g., -7.5% when cb is -15%
    if drawdown_pct < warning_threshold:
        return deny(
            f"Portfolio near circuit breaker: {drawdown_pct*100:.1f}% drawdown from HWM ${hwm:.2f} "
            f"(circuit breaker triggers at {cb_pct*100:.0f}%). "
            "Blocking new trades as precaution.",
            details={
                "portfolio_value": portfolio_value,
                "high_water_mark": hwm,
                "drawdown_pct": round(drawdown_pct, 4),
                "circuit_breaker_pct": cb_pct,
                "warning_threshold": warning_threshold,
            },
        )

    return None


# ---------------------------------------------------------------------------
# Main check function
# ---------------------------------------------------------------------------

def check_trade(
    market_id: str,
    amount: float,
    venue: str = "polymarket",
    side: str = "yes",
    caller: str = "unknown",
) -> dict[str, Any]:
    """
    Run all pre-trade risk checks.

    Args:
        market_id: Market ID to trade on
        amount: Dollar amount to trade
        venue: "polymarket" | "simmer"
        side: "yes" | "no"
        caller: Who is calling this (for logging)

    Returns:
        {"approved": bool, "reason": str, ...extra details}
    """
    config = load_config()
    result: dict[str, Any] = {
        "market_id": market_id,
        "amount": amount,
        "venue": venue,
        "side": side,
        "caller": caller,
        "checks_run": [],
    }

    # --- Check 1: Trading paused ---
    check1 = check_trading_paused(config)
    result["checks_run"].append("trading_paused")
    if check1:
        check1.update(result)
        check1["failed_at_check"] = "trading_paused"
        log_check({"event": "risk_check_denied", **check1})
        return check1

    # Need API data for remaining checks
    # For $SIM trades, most checks are skipped (not real money at risk)
    if venue == "simmer":
        approved = approve("$SIM virtual trade — real-money risk checks skipped")
        approved.update(result)
        log_check({"event": "risk_check_approved_sim", **approved})
        return approved

    # Fetch live data for real money checks
    try:
        creds = load_creds()
        api_key = creds["api_key"]
        portfolio = simmer_get(api_key, "/portfolio")
        pos_data = simmer_get(api_key, "/positions")
        positions = pos_data.get("positions", [])
    except Exception as e:
        denied = deny(f"Cannot fetch live portfolio data to run risk checks: {e}")
        denied.update(result)
        denied["failed_at_check"] = "data_fetch"
        log_check({"event": "risk_check_error", **denied})
        return denied

    # --- Check 2: Position count ---
    check2 = check_position_count(positions, config, venue)
    result["checks_run"].append("position_count")
    if check2:
        check2.update(result)
        check2["failed_at_check"] = "position_count"
        log_check({"event": "risk_check_denied", **check2})
        return check2

    # --- Check 3: Position size ---
    check3 = check_position_size(amount, portfolio, config, venue)
    result["checks_run"].append("position_size")
    if check3:
        check3.update(result)
        check3["failed_at_check"] = "position_size"
        log_check({"event": "risk_check_denied", **check3})
        return check3

    # --- Check 4: Portfolio exposure ---
    check4 = check_portfolio_exposure(amount, portfolio, config, venue)
    result["checks_run"].append("portfolio_exposure")
    if check4:
        check4.update(result)
        check4["failed_at_check"] = "portfolio_exposure"
        log_check({"event": "risk_check_denied", **check4})
        return check4

    # --- Check 5: Circuit breaker proximity ---
    check5 = check_circuit_breaker_proximity(portfolio, config)
    result["checks_run"].append("circuit_breaker_proximity")
    if check5:
        check5.update(result)
        check5["failed_at_check"] = "circuit_breaker_proximity"
        log_check({"event": "risk_check_denied", **check5})
        return check5

    # --- All checks passed ---
    balance_usdc = portfolio.get("balance_usdc", 0) or 0
    total_exposure = portfolio.get("total_exposure", 0) or 0
    portfolio_value = balance_usdc + total_exposure

    approved = approve(
        f"All {len(result['checks_run'])} risk checks passed",
        details={
            "portfolio_value": round(portfolio_value, 4),
            "balance_usdc": balance_usdc,
            "total_exposure": total_exposure,
            "amount": amount,
            "amount_pct_of_portfolio": round(amount / portfolio_value, 4) if portfolio_value > 0 else 0,
        },
    )
    approved.update(result)
    log_check({"event": "risk_check_approved", **approved})
    return approved


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simmer Pre-Trade Risk Check",
        epilog="Returns JSON. Exit code 0=approved, 1=denied.",
    )
    parser.add_argument("--market-id", required=True, help="Market UUID to trade on")
    parser.add_argument("--amount", type=float, required=True, help="Dollar amount")
    parser.add_argument(
        "--venue", default="polymarket", choices=["polymarket", "simmer"],
        help="Trading venue (default: polymarket)",
    )
    parser.add_argument(
        "--side", default="yes", choices=["yes", "no"],
        help="Trade side (default: yes)",
    )
    parser.add_argument("--caller", default="cli", help="Caller identifier for logging")
    args = parser.parse_args()

    result = check_trade(
        market_id=args.market_id,
        amount=args.amount,
        venue=args.venue,
        side=args.side,
        caller=args.caller,
    )

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["approved"] else 1)


if __name__ == "__main__":
    main()
