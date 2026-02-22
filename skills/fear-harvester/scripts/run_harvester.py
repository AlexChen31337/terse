#!/usr/bin/env python3
"""
FearHarvester — unified runner.

Checks Fear & Greed, executes HL spot DCA + Simmer prediction bets on extreme fear.

Usage (cron / manual):
    uv run python scripts/run_harvester.py --paper          # HL paper + Simmer virtual
    uv run python scripts/run_harvester.py --live           # HL live + Simmer virtual
    uv run python scripts/run_harvester.py --dry-run        # simulate everything
    uv run python scripts/run_harvester.py --status         # show positions
    uv run python scripts/run_harvester.py --briefing-only  # Simmer briefing only
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from executor import (  # noqa: E402
    DEFAULT_BUY_THRESHOLD,
    DEFAULT_HOLD_DAYS,
    DEFAULT_SELL_THRESHOLD,
    HLSpotExecutor,
    decide,
    execute_dca_buy,
    execute_rebalance,
    get_btc_price,
    get_fear_greed,
    get_position_summary,
    load_hl_credentials,
    load_state,
    show_status,
)
from simmer_integration import (  # noqa: E402
    _load_client as load_simmer_client,
    execute_fear_trades,
    format_briefing_summary,
    get_briefing,
    manage_positions,
)

logger = logging.getLogger("fear-harvester.runner")

STATE_FILE = Path(__file__).parent.parent / "data" / "runner_state.json"
RUN_LOG_FILE = Path(__file__).parent.parent / "data" / "run_log.jsonl"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def append_run_log(record: dict[str, Any]) -> None:
    """Append a run record to the JSONL log."""
    RUN_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RUN_LOG_FILE, "a") as f:
        f.write(json.dumps(record, default=str) + "\n")


def format_report(
    fg: dict[str, Any],
    btc_price: float,
    hl_action: str,
    hl_result: str,
    simmer_trades: list[dict[str, Any]],
    simmer_briefing: str,
    mode: str,
) -> str:
    """Format a human-readable run report."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S AEDT")
    fg_icon = "🔴" if fg["value"] <= 20 else "🟡" if fg["value"] <= 40 else "🟢"
    lines = [
        f"🌾 FearHarvester Run — {ts}",
        f"   {fg_icon} F&G: {fg['value']} ({fg['label']})",
        f"   BTC: ${btc_price:,.2f}",
        f"   Mode: {mode}",
        "",
        f"📊 HL Spot (UBTC/USDC):",
        f"   Action: {hl_action}",
        f"   Result: {hl_result}",
    ]

    if simmer_trades:
        lines.append("")
        lines.append(f"🎯 Simmer Prediction Markets ({len(simmer_trades)} bets):")
        for t in simmer_trades:
            icon = "✅" if t.get("dry_run") or str(t.get("result", "")).startswith("ok") else "❌"
            lines.append(
                f"   {icon} ${t['amount']:.0f} {t['side'].upper()} — {t['title'][:60]}"
                f" (p={t['yes_prob_at_entry']:.2f})"
            )
    else:
        lines.append("")
        lines.append("🎯 Simmer: No trades this run (F&G above threshold or no suitable markets)")

    if simmer_briefing:
        lines.append("")
        lines.append(simmer_briefing)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="FearHarvester unified runner")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--dry-run", action="store_true", help="Simulate everything, no state changes")
    mode_group.add_argument("--paper", action="store_true", help="Paper HL + virtual Simmer (default)")
    mode_group.add_argument("--live", action="store_true", help="Live HL spot + virtual Simmer")
    parser.add_argument("--status", action="store_true", help="Show positions and P&L, then exit")
    parser.add_argument("--briefing-only", action="store_true", help="Show Simmer briefing, then exit")
    parser.add_argument("--buy-threshold", type=int, default=DEFAULT_BUY_THRESHOLD)
    parser.add_argument("--sell-threshold", type=int, default=DEFAULT_SELL_THRESHOLD)
    parser.add_argument("--hold-days", type=int, default=DEFAULT_HOLD_DAYS)
    parser.add_argument("--dca-amount", type=float, default=500.0)
    parser.add_argument("--max-capital", type=float, default=5000.0)
    parser.add_argument("--simmer-bet", type=float, default=15.0, help="$SIM per Simmer bet")
    parser.add_argument("--simmer-max-bets", type=int, default=3)
    parser.add_argument("--testnet", action="store_true", help="Use HL testnet")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    # --- Mode ---
    if args.live:
        mode = "live"
    elif args.paper:
        mode = "paper"
    else:
        mode = "dry-run"

    # --- Simmer briefing only ---
    if args.briefing_only:
        try:
            client = load_simmer_client()
            briefing = get_briefing(client)
            print(format_briefing_summary(briefing))
        except Exception as e:
            print(f"Simmer briefing failed: {e}")
        return

    # --- Status only ---
    state = load_state()
    if args.status:
        show_status(state)
        return

    config: dict[str, Any] = {
        "buy_threshold": args.buy_threshold,
        "sell_threshold": args.sell_threshold,
        "hold_days": args.hold_days,
        "dca_amount_usd": args.dca_amount,
        "max_capital": args.max_capital,
    }

    # --- Fetch market data ---
    try:
        fg = get_fear_greed()
        btc_price = get_btc_price()
    except Exception as e:
        logger.error("Failed to fetch market data: %s", e)
        sys.exit(1)

    logger.info(
        "F&G=%d (%s) | BTC=$%.2f | Mode=%s",
        fg["value"], fg["label"], btc_price, mode,
    )

    # --- HL Decision ---
    hl_action = decide(fg["value"], state, config)

    # --- HL Executor (live only) ---
    hl_executor = None
    if mode == "live":
        private_key, wallet_address = load_hl_credentials()
        if not private_key:
            logger.error("No HL credentials found. Set HL_PRIVATE_KEY or create .env file.")
            sys.exit(1)
        hl_executor = HLSpotExecutor(
            private_key=private_key,
            wallet_address=wallet_address,
            testnet=args.testnet,
        )

    # --- Execute HL action ---
    hl_result = ""
    if hl_action == "DCA_BUY":
        hl_result = execute_dca_buy(
            btc_price, fg["value"], state, config, mode=mode, hl_executor=hl_executor
        )
    elif hl_action == "REBALANCE_YIELD":
        hl_result = execute_rebalance(
            btc_price, fg["value"], state, config, mode=mode, hl_executor=hl_executor
        )
    else:
        hl_result = (
            f"HOLD — F&G={fg['value']} not in action zone "
            f"(buy≤{config['buy_threshold']}, sell≥{config['sell_threshold']})"
        )

    if hl_executor:
        hl_executor.close()

    # --- Simmer integration ---
    simmer_trades: list[dict[str, Any]] = []
    simmer_briefing = ""

    try:
        simmer_client = load_simmer_client()

        # Always get briefing for heartbeat context
        briefing = get_briefing(simmer_client)
        simmer_briefing = format_briefing_summary(briefing)

        # Run TP/SL management on every cycle (before new trades)
        tpsl_actions = manage_positions(simmer_client, dry_run=(mode == "dry-run"))
        if tpsl_actions:
            logger.info("Simmer TP/SL: %d actions", len(tpsl_actions))
            for a in tpsl_actions:
                logger.info(
                    "  %s %s '%s' (PnL %s) — %s",
                    a["action"], a["side"].upper(), a["title"][:40],
                    a["pnl_pct"], a["reason"],
                )

        # Only open new trades on Simmer during extreme fear
        if fg["value"] <= config["buy_threshold"]:
            simmer_trades = execute_fear_trades(
                fg["value"],
                simmer_client,
                dry_run=(mode == "dry-run"),
                bet_amount=args.simmer_bet,
                max_bets=args.simmer_max_bets,
            )
    except Exception as e:
        logger.warning("Simmer integration error: %s", e)
        simmer_briefing = f"Simmer: unavailable ({e})"

    # --- Report ---
    report = format_report(
        fg, btc_price, hl_action, hl_result, simmer_trades, simmer_briefing, mode
    )
    print(report)

    # --- Log run ---
    run_record = {
        "timestamp": datetime.now().isoformat(),
        "fg": fg,
        "btc_price": btc_price,
        "mode": mode,
        "hl_action": hl_action,
        "hl_result": hl_result,
        "simmer_trades_count": len(simmer_trades),
        "simmer_trades": simmer_trades,
    }
    append_run_log(run_record)


if __name__ == "__main__":
    main()
