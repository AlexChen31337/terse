#!/usr/bin/env python3
"""
Position Guard — Soft SL/TP for Simmer/Polymarket positions.
Checks positions hourly, auto-sells at stop-loss or take-profit levels.

Usage:
    uv run python skills/simmer-risk/position_guard.py check
    uv run python skills/simmer-risk/position_guard.py check --dry-run
    uv run python skills/simmer-risk/position_guard.py status
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

SKILL_DIR = Path(__file__).parent
CONFIG_FILE = SKILL_DIR / "sl_tp_config.json"
LOG_FILE = SKILL_DIR / "data" / "guard_log.jsonl"
CREDS_FILE = Path.home() / ".config" / "simmer" / "credentials.json"
BASE_URL = "https://api.simmer.markets/api/sdk"

DEFAULT_CONFIG = {
    "positions": {
        "59a30946-6c2f-43a0-b2dd-97b2c6892c04": {
            "name": "Anthropic best AI model end of March 2026",
            "side": "yes",
            "shares": 29.78,
            "entry_price": 0.469,
            "stop_loss_price": 0.35,
            "take_profit_price": 0.75,
            "trailing_stop_pct": None,
            "venue": "polymarket",
            "active": True
        }
    },
    "global": {
        "check_interval_minutes": 60,
        "circuit_breaker_loss_pct": -0.15,
        "trading_paused": False,
        "high_water_mark_usdc": 21.73
    }
}


def get_api_key():
    with open(CREDS_FILE) as f:
        return json.load(f)["api_key"]


def api_get(endpoint):
    key = get_api_key()
    req = Request(f"{BASE_URL}/{endpoint}", headers={"Authorization": f"Bearer {key}"})
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except URLError as e:
        print(f"API error: {e}", file=sys.stderr)
        return None


def api_post(endpoint, data):
    key = get_api_key()
    body = json.dumps(data).encode()
    req = Request(
        f"{BASE_URL}/{endpoint}",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except URLError as e:
        print(f"API error: {e}", file=sys.stderr)
        return None


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG


def save_config(config):
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def log_event(event):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    event["ts"] = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
    print(f"[{event['ts'][:19]}] {event.get('action', '?')}: {event.get('message', '')}")


def get_current_positions():
    data = api_get("positions")
    if not data:
        return {}
    positions = {}
    for p in data.get("positions", []):
        positions[p["market_id"]] = p
    return positions


def check_positions(config, dry_run=False):
    current = get_current_positions()
    alerts = []

    for market_id, guard in config["positions"].items():
        if not guard.get("active"):
            continue

        pos = current.get(market_id)
        if not pos:
            log_event({"action": "warn", "market_id": market_id, "message": f"Position not found: {guard['name']}"})
            continue

        side = guard["side"]
        shares_key = f"shares_{side}"
        shares = pos.get(shares_key, 0)
        current_price = pos.get("current_price", 0)
        entry_price = guard["entry_price"]
        sl_price = guard.get("stop_loss_price")
        tp_price = guard.get("take_profit_price")

        # For NO positions, price logic is inverted
        if side == "no":
            effective_price = 1.0 - current_price
        else:
            effective_price = current_price

        pnl_pct = (effective_price - entry_price) / entry_price if entry_price > 0 else 0
        pnl_usd = shares * (effective_price - entry_price)

        status = {
            "name": guard["name"],
            "side": side,
            "shares": shares,
            "entry": entry_price,
            "current": effective_price,
            "pnl_pct": f"{pnl_pct:+.1%}",
            "pnl_usd": f"${pnl_usd:+.2f}",
        }

        # Check stop-loss
        if sl_price and effective_price <= sl_price:
            action_msg = f"🔴 STOP-LOSS HIT: {guard['name']} | Price {effective_price:.3f} <= SL {sl_price:.3f} | PnL: {status['pnl_pct']} ({status['pnl_usd']})"
            alerts.append(action_msg)
            log_event({"action": "stop_loss_triggered", "market_id": market_id, "price": effective_price, "sl": sl_price, "message": action_msg})

            if not dry_run:
                result = execute_sell(market_id, side, shares, guard["venue"])
                log_event({"action": "sell_executed", "market_id": market_id, "result": str(result), "message": f"SL sell: {shares} {side} shares"})
                guard["active"] = False
                save_config(config)
            else:
                print(f"  [DRY-RUN] Would sell {shares} {side} shares")

        # Check take-profit
        elif tp_price and effective_price >= tp_price:
            action_msg = f"🟢 TAKE-PROFIT HIT: {guard['name']} | Price {effective_price:.3f} >= TP {tp_price:.3f} | PnL: {status['pnl_pct']} ({status['pnl_usd']})"
            alerts.append(action_msg)
            log_event({"action": "take_profit_triggered", "market_id": market_id, "price": effective_price, "tp": tp_price, "message": action_msg})

            if not dry_run:
                result = execute_sell(market_id, side, shares, guard["venue"])
                log_event({"action": "sell_executed", "market_id": market_id, "result": str(result), "message": f"TP sell: {shares} {side} shares"})
                guard["active"] = False
                save_config(config)
            else:
                print(f"  [DRY-RUN] Would sell {shares} {side} shares")

        else:
            print(f"  ✅ {guard['name']}: {effective_price:.3f} (SL: {sl_price}, TP: {tp_price}) | {status['pnl_pct']} ({status['pnl_usd']})")

    # Circuit breaker check
    portfolio = api_get("portfolio")
    if portfolio:
        total_value = portfolio.get("balance_usdc", 0) + portfolio.get("total_exposure", 0)
        hwm = config["global"]["high_water_mark_usdc"]
        drawdown = (total_value - hwm) / hwm if hwm > 0 else 0
        cb_threshold = config["global"]["circuit_breaker_loss_pct"]

        if drawdown <= cb_threshold:
            action_msg = f"🚨 CIRCUIT BREAKER: Portfolio ${total_value:.2f} is {drawdown:.1%} below HWM ${hwm:.2f}"
            alerts.append(action_msg)
            log_event({"action": "circuit_breaker", "total_value": total_value, "hwm": hwm, "drawdown": drawdown, "message": action_msg})
            config["global"]["trading_paused"] = True
            save_config(config)

    return alerts


def execute_sell(market_id, side, shares, venue):
    """Attempt to sell via Simmer SDK."""
    result = api_post("trade", {
        "market_id": market_id,
        "side": side,
        "action": "sell",
        "shares": shares,
        "source": "sdk:position-guard"
    })

    if result and not result.get("success"):
        error = result.get("error", "unknown")
        if "Insufficient shares" in error and venue == "polymarket":
            return {"success": False, "error": f"Polymarket position — must sell on Polymarket directly. ALERT OWNER.", "venue": venue}
    return result


def cmd_status(config):
    """Show current guard status."""
    print("=== Position Guard Status ===\n")

    current = get_current_positions()

    for market_id, guard in config["positions"].items():
        pos = current.get(market_id, {})
        side = guard["side"]
        current_price = pos.get("current_price", 0)
        effective_price = (1.0 - current_price) if side == "no" else current_price
        entry = guard["entry_price"]
        pnl_pct = (effective_price - entry) / entry if entry > 0 else 0
        shares = guard["shares"]
        pnl_usd = shares * (effective_price - entry)

        active = "🟢 ACTIVE" if guard.get("active") else "⚪ INACTIVE"
        print(f"{active} {guard['name']}")
        print(f"  Side: {side} | Shares: {shares}")
        print(f"  Entry: ${entry:.3f} | Current: ${effective_price:.3f}")
        print(f"  PnL: {pnl_pct:+.1%} (${pnl_usd:+.2f})")
        print(f"  SL: ${guard.get('stop_loss_price', 'none')} | TP: ${guard.get('take_profit_price', 'none')}")
        print(f"  Venue: {guard.get('venue', '?')}")
        print()

    g = config["global"]
    paused = "🚨 YES" if g.get("trading_paused") else "✅ No"
    print(f"Trading paused: {paused}")
    print(f"Circuit breaker: {g['circuit_breaker_loss_pct']:.0%}")
    print(f"High water mark: ${g['high_water_mark_usdc']:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Position Guard — SL/TP monitor")
    sub = parser.add_subparsers(dest="command")

    check_p = sub.add_parser("check", help="Check positions against SL/TP")
    check_p.add_argument("--dry-run", action="store_true")

    sub.add_parser("status", help="Show guard status")

    args = parser.parse_args()
    config = load_config()

    if args.command == "check":
        alerts = check_positions(config, dry_run=args.dry_run)
        if alerts:
            print("\n⚠️ ALERTS:")
            for a in alerts:
                print(f"  {a}")
        else:
            print("\n✅ All positions within bounds.")
    elif args.command == "status":
        cmd_status(config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
