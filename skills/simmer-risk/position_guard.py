#!/usr/bin/env python3
"""
Position Guard v2 — Auto-discovering SL/TP for Simmer/Polymarket positions.

Features:
  - Auto-registers new positions from Simmer API with default preset SL/TP
  - Per-position SL/TP with preset tiers (conservative/moderate/aggressive)
  - Trailing stop support
  - Circuit breaker (portfolio-level)
  - Integrates with risk_config.json for global limits

Usage:
    uv run python skills/simmer-risk/position_guard.py check
    uv run python skills/simmer-risk/position_guard.py check --dry-run
    uv run python skills/simmer-risk/position_guard.py status
    uv run python skills/simmer-risk/position_guard.py sync          # force sync from API
    uv run python skills/simmer-risk/position_guard.py set-preset MARKET_ID conservative
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

SKILL_DIR = Path(__file__).parent
CONFIG_FILE = SKILL_DIR / "sl_tp_config.json"
RISK_CONFIG_FILE = SKILL_DIR / "risk_config.json"
LOG_FILE = SKILL_DIR / "data" / "guard_log.jsonl"
CREDS_FILE = Path.home() / ".config" / "simmer" / "credentials.json"
BASE_URL = "https://api.simmer.markets/api/sdk"


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

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
        print(f"API error ({endpoint}): {e}", file=sys.stderr)
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
        print(f"API error ({endpoint}): {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Config management
# ---------------------------------------------------------------------------

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        # Ensure presets exist (migration from v1)
        if "presets" not in cfg:
            cfg["presets"] = DEFAULT_PRESETS
            cfg["default_preset"] = "moderate"
            cfg["auto_register"] = True
            save_config(cfg)
        return cfg
    cfg = {
        "presets": DEFAULT_PRESETS,
        "default_preset": "moderate",
        "auto_register": True,
        "positions": {},
        "global": {
            "check_interval_minutes": 60,
            "circuit_breaker_loss_pct": -0.15,
            "trading_paused": False,
            "high_water_mark_usdc": 21.59,
        }
    }
    save_config(cfg)
    return cfg


def load_risk_config():
    if RISK_CONFIG_FILE.exists():
        with open(RISK_CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(config):
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


DEFAULT_PRESETS = {
    "conservative": {"sl_pct": -15, "tp_pct": 60, "trailing_stop_pct": 10},
    "moderate": {"sl_pct": -25, "tp_pct": 80, "trailing_stop_pct": None},
    "aggressive": {"sl_pct": -40, "tp_pct": 120, "trailing_stop_pct": None},
}


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_event(event):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    event["ts"] = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
    print(f"[{event['ts'][:19]}] {event.get('action', '?')}: {event.get('message', '')}")


# ---------------------------------------------------------------------------
# Preset helpers
# ---------------------------------------------------------------------------

def apply_preset(entry_price, preset_name, presets):
    """Calculate SL/TP prices from a preset and entry price."""
    preset = presets.get(preset_name, presets.get("moderate", DEFAULT_PRESETS["moderate"]))
    sl_price = round(entry_price * (1 + preset["sl_pct"] / 100), 4)
    tp_price = round(entry_price * (1 + preset["tp_pct"] / 100), 4)
    # Clamp to [0.01, 0.99] for prediction markets
    sl_price = max(0.01, min(0.99, sl_price))
    tp_price = max(0.01, min(0.99, tp_price))
    return {
        "stop_loss_price": sl_price,
        "take_profit_price": tp_price,
        "trailing_stop_pct": preset.get("trailing_stop_pct"),
        "preset": preset_name,
    }


# ---------------------------------------------------------------------------
# Auto-discovery: sync positions from Simmer API
# ---------------------------------------------------------------------------

def sync_positions(config, verbose=True):
    """Fetch live positions from Simmer API, auto-register any new ones."""
    data = api_get("positions")
    if not data:
        if verbose:
            print("⚠️  Could not fetch positions from API")
        return 0

    positions_list = data.get("positions", [])
    presets = config.get("presets", DEFAULT_PRESETS)
    default_preset = config.get("default_preset", "moderate")
    new_count = 0

    for pos in positions_list:
        market_id = pos.get("market_id", "")
        if not market_id:
            continue

        # Determine if position has shares (yes or no side)
        shares_yes = pos.get("shares_yes", 0) or 0
        shares_no = pos.get("shares_no", 0) or 0

        if shares_yes <= 0 and shares_no <= 0:
            continue  # No active position

        side = "yes" if shares_yes > shares_no else "no"
        shares = shares_yes if side == "yes" else shares_no

        # Skip if already tracked
        if market_id in config["positions"]:
            existing = config["positions"][market_id]
            # Update shares count if changed
            if existing.get("shares") != shares:
                existing["shares"] = shares
                if verbose:
                    print(f"  📝 Updated shares for {existing.get('name', market_id)}: {shares}")
            # Reactivate if was inactive but now has shares
            if not existing.get("active") and shares > 0:
                existing["active"] = True
                if verbose:
                    print(f"  🔄 Reactivated: {existing.get('name', market_id)}")
            continue

        # New position — auto-register with default preset
        current_price = pos.get("current_price", 0)
        # Estimate entry price from cost basis if available, otherwise use current
        cost_basis = pos.get("cost_basis", 0)
        if cost_basis and shares > 0:
            entry_price = round(cost_basis / shares, 4)
        else:
            entry_price = current_price

        if entry_price <= 0:
            entry_price = current_price

        sl_tp = apply_preset(entry_price, default_preset, presets)

        config["positions"][market_id] = {
            "name": pos.get("question", pos.get("title", market_id[:20])),
            "side": side,
            "shares": shares,
            "entry_price": entry_price,
            "stop_loss_price": sl_tp["stop_loss_price"],
            "take_profit_price": sl_tp["take_profit_price"],
            "trailing_stop_pct": sl_tp["trailing_stop_pct"],
            "preset": default_preset,
            "venue": pos.get("venue", "polymarket"),
            "active": True,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }

        new_count += 1
        if verbose:
            print(f"  🆕 Auto-registered: {config['positions'][market_id]['name']}")
            print(f"     Side: {side} | Entry: ${entry_price:.3f} | SL: ${sl_tp['stop_loss_price']:.3f} | TP: ${sl_tp['take_profit_price']:.3f} | Preset: {default_preset}")

        log_event({
            "action": "auto_register",
            "market_id": market_id,
            "name": config["positions"][market_id]["name"],
            "preset": default_preset,
            "entry_price": entry_price,
            "sl": sl_tp["stop_loss_price"],
            "tp": sl_tp["take_profit_price"],
            "message": f"Auto-registered new position with {default_preset} preset",
        })

    # Mark positions as inactive if no longer in API
    live_ids = {p.get("market_id") for p in positions_list}
    for market_id, guard in config["positions"].items():
        if guard.get("active") and market_id not in live_ids:
            guard["active"] = False
            if verbose:
                print(f"  ⚪ Deactivated (no longer in portfolio): {guard.get('name', market_id)}")

    if new_count > 0 or True:  # Always save to persist share updates
        save_config(config)

    if verbose:
        total_active = sum(1 for p in config["positions"].values() if p.get("active"))
        print(f"\n📊 Sync complete: {new_count} new, {total_active} active, {len(config['positions'])} total tracked")

    return new_count


# ---------------------------------------------------------------------------
# Position checking with SL/TP + trailing stop
# ---------------------------------------------------------------------------

def get_current_positions():
    data = api_get("positions")
    if not data:
        return {}
    return {p["market_id"]: p for p in data.get("positions", [])}


def check_positions(config, dry_run=False):
    """Check all tracked positions against SL/TP levels."""
    # Auto-sync first if enabled
    if config.get("auto_register", True):
        sync_positions(config, verbose=False)

    current = get_current_positions()
    alerts = []
    risk_cfg = load_risk_config()

    for market_id, guard in config["positions"].items():
        if not guard.get("active"):
            continue

        pos = current.get(market_id)
        if not pos:
            continue

        side = guard["side"]
        shares = guard.get("shares", 0)
        current_price = pos.get("current_price", 0)
        entry_price = guard["entry_price"]
        sl_price = guard.get("stop_loss_price")
        tp_price = guard.get("take_profit_price")

        # For NO positions, price logic is inverted
        effective_price = (1.0 - current_price) if side == "no" else current_price

        if entry_price <= 0:
            continue

        pnl_pct = (effective_price - entry_price) / entry_price
        pnl_usd = shares * (effective_price - entry_price)

        # Trailing stop update
        trailing_pct = guard.get("trailing_stop_pct")
        if trailing_pct and effective_price > entry_price:
            high_water = guard.get("high_water_price", entry_price)
            if effective_price > high_water:
                guard["high_water_price"] = effective_price
                new_sl = round(effective_price * (1 - trailing_pct / 100), 4)
                if sl_price is None or new_sl > sl_price:
                    guard["stop_loss_price"] = new_sl
                    sl_price = new_sl
                    log_event({
                        "action": "trailing_stop_update",
                        "market_id": market_id,
                        "new_sl": new_sl,
                        "high_water": effective_price,
                        "message": f"Trailing stop raised to ${new_sl:.3f} (HW: ${effective_price:.3f})"
                    })
                save_config(config)

        # Check stop-loss
        if sl_price and effective_price <= sl_price:
            action_msg = f"🔴 STOP-LOSS HIT: {guard['name']} | Price {effective_price:.3f} <= SL {sl_price:.3f} | PnL: {pnl_pct:+.1%} (${pnl_usd:+.2f})"
            alerts.append(action_msg)
            log_event({"action": "stop_loss_triggered", "market_id": market_id, "price": effective_price, "sl": sl_price, "message": action_msg})

            if not dry_run:
                result = execute_sell(market_id, side, shares, guard.get("venue", "polymarket"))
                log_event({"action": "sell_executed", "market_id": market_id, "result": str(result), "message": f"SL sell: {shares} {side} shares"})
                guard["active"] = False
                # Update daily P&L in risk_config
                update_daily_pnl(risk_cfg, pnl_usd, is_loss=True)
                save_config(config)
            else:
                print(f"  [DRY-RUN] Would sell {shares} {side} shares")

        # Check take-profit
        elif tp_price and effective_price >= tp_price:
            action_msg = f"🟢 TAKE-PROFIT HIT: {guard['name']} | Price {effective_price:.3f} >= TP {tp_price:.3f} | PnL: {pnl_pct:+.1%} (${pnl_usd:+.2f})"
            alerts.append(action_msg)
            log_event({"action": "take_profit_triggered", "market_id": market_id, "price": effective_price, "tp": tp_price, "message": action_msg})

            if not dry_run:
                result = execute_sell(market_id, side, shares, guard.get("venue", "polymarket"))
                log_event({"action": "sell_executed", "market_id": market_id, "result": str(result), "message": f"TP sell: {shares} {side} shares"})
                guard["active"] = False
                update_daily_pnl(risk_cfg, pnl_usd, is_loss=False)
                save_config(config)
            else:
                print(f"  [DRY-RUN] Would sell {shares} {side} shares")

        else:
            print(f"  ✅ {guard['name']}: ${effective_price:.3f} (SL: ${sl_price}, TP: ${tp_price}) | {pnl_pct:+.1%} (${pnl_usd:+.2f})")

    # Circuit breaker check
    portfolio = api_get("portfolio")
    if portfolio:
        total_value = portfolio.get("balance_usdc", 0) + portfolio.get("total_exposure", 0)
        hwm = config["global"].get("high_water_mark_usdc", 0)
        if hwm > 0:
            drawdown = (total_value - hwm) / hwm
            cb_threshold = config["global"].get("circuit_breaker_loss_pct", -0.15)
            if drawdown <= cb_threshold:
                action_msg = f"🚨 CIRCUIT BREAKER: Portfolio ${total_value:.2f} is {drawdown:.1%} below HWM ${hwm:.2f}"
                alerts.append(action_msg)
                log_event({"action": "circuit_breaker", "total_value": total_value, "hwm": hwm, "drawdown": drawdown, "message": action_msg})
                config["global"]["trading_paused"] = True
                save_config(config)
            # Update HWM if new high
            elif total_value > hwm:
                config["global"]["high_water_mark_usdc"] = round(total_value, 2)
                save_config(config)

    return alerts


def update_daily_pnl(risk_cfg, pnl_usd, is_loss):
    """Update daily P&L tracking in risk_config.json."""
    if not risk_cfg:
        return
    state = risk_cfg.get("state", {})
    state["today_pnl_usd"] = round(state.get("today_pnl_usd", 0) + pnl_usd, 2)
    state["today_trades"] = state.get("today_trades", 0) + 1
    if is_loss:
        state["consecutive_losses"] = state.get("consecutive_losses", 0) + 1
        # Check circuit breaker
        cb = risk_cfg.get("circuit_breakers", {})
        if state["consecutive_losses"] >= cb.get("consecutive_losses", 3):
            state["trading_paused"] = True
    else:
        state["consecutive_losses"] = 0

    # Check daily stop-loss
    targets = risk_cfg.get("profit_targets", {})
    if state["today_pnl_usd"] <= targets.get("daily_stop_loss_usd", -3.0):
        state["trading_paused"] = True

    risk_cfg["state"] = state
    with open(RISK_CONFIG_FILE, "w") as f:
        json.dump(risk_cfg, f, indent=2)


def execute_sell(market_id, side, shares, venue):
    """Attempt to sell via Simmer SDK."""
    result = api_post("trade", {
        "market_id": market_id,
        "side": side,
        "action": "sell",
        "shares": shares,
        "source": "sdk:position-guard-v2"
    })
    if result and not result.get("success"):
        error = result.get("error", "unknown")
        if "Insufficient shares" in error and venue == "polymarket":
            return {"success": False, "error": f"Polymarket position — must sell on Polymarket directly. ALERT OWNER.", "venue": venue}
    return result


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def cmd_status(config):
    """Show current guard status with all tracked positions."""
    print("=== Position Guard v2 — Status ===\n")

    # Show presets
    print("📋 Presets:")
    for name, p in config.get("presets", {}).items():
        default = " (DEFAULT)" if name == config.get("default_preset") else ""
        trail = f" / Trail {p['trailing_stop_pct']}%" if p.get('trailing_stop_pct') else ''
        print(f"  {name}{default}: SL {p['sl_pct']}% / TP +{p['tp_pct']}%{trail}")
    print()

    # Sync and show positions
    current = get_current_positions()
    active_count = 0
    inactive_count = 0

    for market_id, guard in config["positions"].items():
        pos = current.get(market_id, {})
        side = guard["side"]
        current_price = pos.get("current_price", 0)
        effective_price = (1.0 - current_price) if side == "no" else current_price
        entry = guard["entry_price"]
        pnl_pct = (effective_price - entry) / entry if entry > 0 else 0
        shares = guard.get("shares", 0)
        pnl_usd = shares * (effective_price - entry)

        if guard.get("active"):
            active_count += 1
            icon = "🟢"
        else:
            inactive_count += 1
            icon = "⚪"

        print(f"{icon} {guard.get('name', market_id)}")
        print(f"  Side: {side} | Shares: {shares:.2f} | Preset: {guard.get('preset', '?')}")
        print(f"  Entry: ${entry:.3f} | Current: ${effective_price:.3f} | PnL: {pnl_pct:+.1%} (${pnl_usd:+.2f})")
        print(f"  SL: ${guard.get('stop_loss_price', 'none')} | TP: ${guard.get('take_profit_price', 'none')}")
        if guard.get("trailing_stop_pct"):
            print(f"  Trailing: {guard['trailing_stop_pct']}% | HW: ${guard.get('high_water_price', entry):.3f}")
        print()

    if not config["positions"]:
        print("  (no positions tracked)\n")

    g = config["global"]
    paused = "🚨 YES" if g.get("trading_paused") else "✅ No"
    auto_reg = "✅ On" if config.get("auto_register") else "❌ Off"
    print(f"Auto-register: {auto_reg} | Default preset: {config.get('default_preset', '?')}")
    print(f"Trading paused: {paused}")
    print(f"Circuit breaker: {g.get('circuit_breaker_loss_pct', -0.15):.0%}")
    print(f"High water mark: ${g.get('high_water_mark_usdc', 0):.2f}")
    print(f"Positions: {active_count} active / {inactive_count} inactive / {len(config['positions'])} total")


def cmd_set_preset(config, market_id, preset_name):
    """Change preset for a specific position."""
    if market_id not in config["positions"]:
        # Try partial match
        matches = [k for k in config["positions"] if market_id in k]
        if len(matches) == 1:
            market_id = matches[0]
        else:
            print(f"❌ Position not found: {market_id}")
            return

    presets = config.get("presets", DEFAULT_PRESETS)
    if preset_name not in presets:
        print(f"❌ Unknown preset: {preset_name}. Available: {list(presets.keys())}")
        return

    guard = config["positions"][market_id]
    entry_price = guard["entry_price"]
    sl_tp = apply_preset(entry_price, preset_name, presets)

    guard["stop_loss_price"] = sl_tp["stop_loss_price"]
    guard["take_profit_price"] = sl_tp["take_profit_price"]
    guard["trailing_stop_pct"] = sl_tp["trailing_stop_pct"]
    guard["preset"] = preset_name
    save_config(config)

    print(f"✅ {guard['name']} → {preset_name}")
    print(f"   SL: ${sl_tp['stop_loss_price']:.3f} | TP: ${sl_tp['take_profit_price']:.3f}")
    if sl_tp["trailing_stop_pct"]:
        print(f"   Trailing: {sl_tp['trailing_stop_pct']}%")


def main():
    parser = argparse.ArgumentParser(description="Position Guard v2 — Auto-discovering SL/TP monitor")
    sub = parser.add_subparsers(dest="command")

    check_p = sub.add_parser("check", help="Check positions against SL/TP")
    check_p.add_argument("--dry-run", action="store_true")

    sub.add_parser("status", help="Show guard status")
    sub.add_parser("sync", help="Force sync positions from Simmer API")

    preset_p = sub.add_parser("set-preset", help="Change preset for a position")
    preset_p.add_argument("market_id", help="Market ID (or partial match)")
    preset_p.add_argument("preset", help="Preset name: conservative, moderate, aggressive")

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
        sync_positions(config, verbose=True)
        config = load_config()  # Reload after sync
        cmd_status(config)
    elif args.command == "sync":
        sync_positions(config, verbose=True)
    elif args.command == "set-preset":
        cmd_set_preset(config, args.market_id, args.preset)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
