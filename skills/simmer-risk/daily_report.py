#!/usr/bin/env python3
"""
Simmer Daily P&L Report — Run every morning at 9 AM AEDT.

Outputs:
  - Portfolio summary (real money vs sim money)
  - Position-by-position breakdown
  - Today's trades
  - Unrealized P&L
  - Win/loss ratio (from monitor log)
  - Stop-loss proximity alerts

Usage:
    uv run python daily_report.py
    uv run python daily_report.py --json    # machine-readable output
    uv run python daily_report.py --days 7  # include last 7 days of trades
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
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


def simmer_get(api_key: str, path: str, params: Optional[dict] = None) -> dict[str, Any]:
    resp = requests.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        headers={"Authorization": f"Bearer {api_key}"},
        params=params or {},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def fmt_pct(value: float, decimals: int = 1) -> str:
    return f"{value*100:+.{decimals}f}%"


def fmt_currency(value: float, symbol: str = "$") -> str:
    return f"{symbol}{value:.2f}"


def compute_pnl_pct(position: dict[str, Any]) -> Optional[float]:
    cost_basis = position.get("cost_basis", 0) or 0
    pnl = position.get("pnl", 0) or 0
    if cost_basis <= 0:
        return None
    return pnl / cost_basis


# ---------------------------------------------------------------------------
# Monitor log analysis
# ---------------------------------------------------------------------------

def read_monitor_log(since: datetime) -> list[dict[str, Any]]:
    """Read monitor log events since a given time."""
    if not LOG_PATH.exists():
        return []

    events = []
    try:
        for line in LOG_PATH.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                ts_str = event.get("timestamp", "")
                if ts_str:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts >= since:
                        events.append(event)
            except Exception:
                continue
    except Exception:
        pass
    return events


def compute_win_loss_from_log(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute win/loss ratio from monitor log events."""
    stop_losses = [e for e in events if e.get("event") == "stop_loss_triggered"]
    take_profits = [e for e in events if e.get("event") == "take_profit_triggered"]
    circuit_breakers = [e for e in events if e.get("event") == "circuit_breaker_triggered"]

    total_wins = len(take_profits)
    total_losses = len(stop_losses)
    total_actions = total_wins + total_losses

    ratio = total_wins / total_actions if total_actions > 0 else None

    return {
        "stop_losses": len(stop_losses),
        "take_profits": len(take_profits),
        "circuit_breakers": len(circuit_breakers),
        "win_rate": ratio,
        "total_risk_events": total_actions,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(api_key: str, config: dict[str, Any], days: int = 1) -> dict[str, Any]:
    """Fetch all data and build the report dict."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Fetch portfolio
    portfolio = simmer_get(api_key, "/portfolio")

    # Fetch positions
    pos_data = simmer_get(api_key, "/positions")
    positions = pos_data.get("positions", [])

    # Fetch recent trades (today's)
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        trades_data = simmer_get(api_key, "/trades", {"limit": 50, "since": since_str})
        recent_trades = trades_data.get("trades", [])
    except Exception:
        recent_trades = []

    # Monitor log analysis
    log_events = read_monitor_log(since)
    win_loss = compute_win_loss_from_log(log_events)

    # Determine active positions:
    # - Simmer positions have explicit "status" field ("active" / "resolved")
    # - Polymarket positions have NO status field — treat as active if they have shares
    def is_active(p: dict[str, Any]) -> bool:
        status = p.get("status")
        if status is not None:
            return status == "active"
        # No status field: check if it has shares (Polymarket style)
        shares = (p.get("shares_yes") or 0) + (p.get("shares_no") or 0)
        return shares > 0

    # Separate positions by venue
    active_positions = [p for p in positions if is_active(p)]
    resolved_positions = [p for p in positions if not is_active(p)]

    real_money_positions = [
        p for p in active_positions
        if p.get("venue") == "polymarket" and p.get("currency") == "USDC"
    ]
    sim_positions = [
        p for p in active_positions
        if p.get("venue") == "simmer"
    ]

    # P&L analysis
    real_pnl = sum(p.get("pnl", 0) or 0 for p in real_money_positions)
    sim_pnl = sum(p.get("pnl", 0) or 0 for p in sim_positions)

    # High-water mark and circuit breaker status
    hwm = config.get("high_water_mark", 18.0)
    cb_pct = config.get("circuit_breaker_pct", -0.15)
    balance_usdc = portfolio.get("balance_usdc", 0) or 0
    total_exposure = portfolio.get("total_exposure", 0) or 0
    portfolio_value = balance_usdc + total_exposure
    drawdown_from_hwm = (portfolio_value - hwm) / hwm if hwm > 0 else 0

    # Stop-loss proximity (positions within 75% of stop-loss)
    stop_loss_pct = config.get("stop_loss_pct", -0.20)
    positions_near_sl: list[dict[str, Any]] = []
    for pos in real_money_positions:
        pnl_pct = compute_pnl_pct(pos)
        if pnl_pct is not None and pnl_pct < (stop_loss_pct * 0.75):
            positions_near_sl.append({
                "market_id": pos.get("market_id"),
                "question": pos.get("question", "")[:80],
                "pnl_pct": pnl_pct,
                "stop_loss_pct": stop_loss_pct,
                "current_value": pos.get("current_value"),
            })

    return {
        "generated_at": now_iso(),
        "period_days": days,
        "trading_paused": config.get("trading_paused", False),

        "portfolio": {
            "balance_usdc": balance_usdc,
            "total_exposure_usdc": total_exposure,
            "total_value_usdc": round(portfolio_value, 4),
            "high_water_mark": hwm,
            "drawdown_from_hwm_pct": round(drawdown_from_hwm, 4),
            "circuit_breaker_threshold": cb_pct,
            "circuit_breaker_proximity": round(drawdown_from_hwm / cb_pct, 2) if cb_pct != 0 else 0,
            "real_positions_count": len(real_money_positions),
            "sim_positions_count": len(sim_positions),
            "pnl_total": portfolio.get("pnl_total"),
            "polymarket_pnl": portfolio.get("polymarket_pnl"),
            "sim_pnl": portfolio.get("pnl_total", 0) - (portfolio.get("polymarket_pnl") or 0),
        },

        "real_money_positions": [
            {
                "market_id": p.get("market_id"),
                "question": p.get("question", "")[:100],
                "venue": p.get("venue"),
                "current_value": p.get("current_value"),
                "cost_basis": p.get("cost_basis"),
                "pnl": p.get("pnl"),
                "pnl_pct": compute_pnl_pct(p),
                "current_probability": p.get("current_probability"),
                "resolves_at": p.get("resolves_at"),
                "near_stop_loss": compute_pnl_pct(p) is not None and (compute_pnl_pct(p) or 0) < (stop_loss_pct * 0.75),
            }
            for p in real_money_positions
        ],

        "sim_pnl_summary": {
            "active_positions": len(sim_positions),
            "total_sim_pnl": sim_pnl,
            "note": "Virtual $SIM — educational only, not real money",
        },

        "recent_trades": [
            {
                "created_at": t.get("created_at"),
                "market_question": t.get("market_question", "")[:80],
                "side": t.get("side"),
                "action": t.get("action"),
                "cost": t.get("cost"),
                "venue": t.get("venue"),
                "source": t.get("source"),
            }
            for t in recent_trades[:20]
        ],

        "risk_events": win_loss,
        "positions_near_stop_loss": positions_near_sl,

        "risk_config": {
            "stop_loss_pct": config.get("stop_loss_pct"),
            "take_profit_pct": config.get("take_profit_pct"),
            "max_position_pct": config.get("max_position_pct"),
            "max_positions": config.get("max_positions"),
            "circuit_breaker_pct": cb_pct,
        },
    }


def print_report(report: dict[str, Any]) -> None:
    """Print human-readable report to stdout."""
    p = report["portfolio"]
    sep = "=" * 65

    print(f"\n{sep}")
    print(f"  📊 SIMMER RISK REPORT — {report['generated_at'][:10]}")
    print(sep)

    if report.get("trading_paused"):
        print("  🚨 WARNING: TRADING IS PAUSED (circuit breaker active)")
        print()

    # Portfolio overview
    print("\n📁 PORTFOLIO (Real Money / USDC)")
    print(f"  Cash:          ${p['balance_usdc']:.2f}")
    print(f"  Open exposure: ${p['total_exposure_usdc']:.2f}")
    print(f"  Total value:   ${p['total_value_usdc']:.2f}")
    print(f"  High-water mark: ${p['high_water_mark']:.2f}")

    drawdown_label = fmt_pct(p['drawdown_from_hwm_pct'])
    cb_prox = p['circuit_breaker_proximity']
    cb_emoji = "🔴" if cb_prox >= 0.75 else "🟡" if cb_prox >= 0.50 else "🟢"
    print(f"  Drawdown vs HWM: {drawdown_label} {cb_emoji} ({cb_prox*100:.0f}% of way to circuit breaker)")
    print(f"  Polymarket P&L: {fmt_currency(p.get('polymarket_pnl') or 0)}")

    # Real money positions
    print(f"\n💵 REAL MONEY POSITIONS ({p['real_positions_count']} active)")
    real_positions = report.get("real_money_positions", [])
    if not real_positions:
        print("  (none)")
    else:
        for pos in real_positions:
            pnl_pct = pos.get("pnl_pct")
            pnl_label = fmt_pct(pnl_pct) if pnl_pct is not None else "N/A"
            sl_warn = " ⚠️ NEAR STOP-LOSS" if pos.get("near_stop_loss") else ""
            prob = pos.get("current_probability")
            prob_label = f"({prob*100:.0f}% prob)" if prob is not None else ""
            print(f"  • {pos['question'][:60]}")
            print(f"    Value: ${pos.get('current_value', 0):.2f} | "
                  f"Cost: ${pos.get('cost_basis', 0):.2f} | "
                  f"P&L: ${pos.get('pnl', 0):.2f} ({pnl_label}) {prob_label}{sl_warn}")
            if pos.get("resolves_at"):
                print(f"    Resolves: {pos['resolves_at'][:10]}")

    # Sim positions summary
    sim = report.get("sim_pnl_summary", {})
    print(f"\n🎮 SIM POSITIONS ({sim.get('active_positions', 0)} active)")
    print(f"  Total $SIM P&L: {sim.get('total_sim_pnl', 0):.2f}")
    print(f"  Note: {sim.get('note', '')}")

    # Today's trades
    recent_trades = report.get("recent_trades", [])
    period = report.get("period_days", 1)
    print(f"\n📋 RECENT TRADES (last {period} day(s)) — {len(recent_trades)} found")
    if not recent_trades:
        print("  (no trades)")
    else:
        for t in recent_trades[:10]:
            ts = t.get("created_at", "")[:16]
            action = (t.get("action") or "buy").upper()
            side = t.get("side", "?").upper()
            cost = t.get("cost") or 0
            venue = t.get("venue", "?")
            source = t.get("source", "?")
            print(f"  [{ts}] {action} {side} ${cost:.2f} on {venue} via {source}")
            print(f"    {t.get('market_question', '')[:60]}")

    # Risk events
    events = report.get("risk_events", {})
    print(f"\n🛡️  RISK EVENTS (last {period} day(s))")
    print(f"  Stop-losses triggered:  {events.get('stop_losses', 0)}")
    print(f"  Take-profits triggered: {events.get('take_profits', 0)}")
    print(f"  Circuit breakers:       {events.get('circuit_breakers', 0)}")
    win_rate = events.get("win_rate")
    if win_rate is not None:
        print(f"  Win rate (by risk events): {win_rate*100:.1f}%")

    # Stop-loss warnings
    near_sl = report.get("positions_near_stop_loss", [])
    if near_sl:
        print(f"\n⚠️  STOP-LOSS WARNINGS ({len(near_sl)} positions)")
        for pos in near_sl:
            pnl_label = fmt_pct(pos.get("pnl_pct", 0))
            sl_label = fmt_pct(pos.get("stop_loss_pct", -0.20))
            print(f"  • {pos['question'][:60]}")
            print(f"    P&L: {pnl_label} (stop-loss at {sl_label})")

    # Risk config
    rc = report.get("risk_config", {})
    print(f"\n⚙️  RISK SETTINGS")
    print(f"  Stop-loss:         {fmt_pct(rc.get('stop_loss_pct', -0.20))}")
    print(f"  Take-profit:       {fmt_pct(rc.get('take_profit_pct', 0.50))}")
    print(f"  Max position size: {fmt_pct(rc.get('max_position_pct', 0.30))}")
    print(f"  Max positions:     {rc.get('max_positions', 5)}")
    print(f"  Circuit breaker:   {fmt_pct(rc.get('circuit_breaker_pct', -0.15))}")

    print(f"\n{sep}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Simmer Daily P&L Report")
    parser.add_argument(
        "--json", action="store_true",
        help="Output machine-readable JSON instead of human text",
    )
    parser.add_argument(
        "--days", type=int, default=1,
        help="Include trades from last N days (default: 1)",
    )
    args = parser.parse_args()

    creds = load_creds()
    config = load_config()
    report = generate_report(creds["api_key"], config, days=args.days)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
