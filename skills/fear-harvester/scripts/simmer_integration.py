#!/usr/bin/env python3
"""
Simmer Prediction Market integration for FearHarvester.

When F&G enters extreme fear (≤ 20), we take contrarian positions on Simmer:
  - YES on crypto recovery markets ("Will BTC be above $X by date?")
  - YES on fear index normalization markets ("Will F&G reach 30+ this month?")
  - NO on extreme crash continuation markets (contrarian — dips get bought)

When F&G recovers (≥ 60 Greed), we look to close/take profit on open positions.

Uses virtual $SIM by default (safe). Real money (Polymarket/Kalshi) requires
Bowen to claim the agent at https://simmer.markets/claim/leaf-7IPH.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Add Simmer SDK to path
SIMMER_VENV = Path("/home/bowen/clawd/skills/simmer/.venv/lib/python3.11/site-packages")
if str(SIMMER_VENV) not in sys.path:
    sys.path.insert(0, str(SIMMER_VENV))

SIMMER_CREDS_PATH = Path.home() / ".config/simmer/credentials.json"

logger = logging.getLogger("fear-harvester.simmer")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BET_PER_MARKET = 15.0       # $SIM per bet
MAX_BETS_PER_RUN = 3        # Max markets to bet on per F&G check
MIN_MARKET_VOLUME = 50.0    # Skip thin markets
MIN_YES_PROB = 0.25         # Don't bet YES if probability already > 75% (low edge)
MAX_YES_PROB = 0.75

# Keywords for finding relevant markets
RECOVERY_KEYWORDS = [
    "bitcoin", "btc", "crypto", "fear greed", "cryptocurrency",
    "ethereum", "eth", "bull", "recovery",
]
CRASH_KEYWORDS = ["crash", "bear", "below", "collapse", "dump"]


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def _load_client():
    """Load Simmer SDK client from credentials."""
    try:
        from simmer_sdk import SimmerClient  # type: ignore[import-not-found]
        creds = json.loads(SIMMER_CREDS_PATH.read_text())
        return SimmerClient(api_key=creds["api_key"])
    except ImportError:
        raise RuntimeError("Simmer SDK not found. Run: pip install simmer-sdk")
    except FileNotFoundError:
        raise RuntimeError(f"Simmer credentials not found at {SIMMER_CREDS_PATH}")


# ---------------------------------------------------------------------------
# Market discovery
# ---------------------------------------------------------------------------

def find_fear_markets(client: Any) -> list[Any]:
    """
    Find crypto markets relevant to a fear-based contrarian trade.

    Returns markets sorted by volume (descending).
    """
    candidates = []
    seen_ids: set[str] = set()

    for keyword in ["bitcoin", "crypto", "btc", "fear"]:
        try:
            markets = client.find_markets(keyword)
            for m in (markets or []):
                mid = str(getattr(m, "market_id", None) or getattr(m, "id", id(m)))
                if mid not in seen_ids:
                    seen_ids.add(mid)
                    candidates.append(m)
        except Exception as e:
            logger.warning("Simmer market search failed for '%s': %s", keyword, e)

    return candidates


def _market_attr(market: Any, *keys: str, default: Any = None) -> Any:
    """Get attribute from a Market/Position object or dict."""
    for key in keys:
        if isinstance(market, dict):
            val = market.get(key)
        else:
            val = getattr(market, key, None)
        if val is not None:
            return val
    return default


def _get_yes_prob(market: Any) -> Optional[float]:
    """Extract YES probability from a Market object or dict."""
    # SDK Market object uses current_probability
    for key in ("current_probability", "yes_price", "yes_prob", "probability", "external_price_yes"):
        val = _market_attr(market, key)
        if val is not None:
            try:
                p = float(val)
                return p if p <= 1.0 else p / 100.0
            except (TypeError, ValueError):
                continue
    return None


def classify_market(market: Any) -> Optional[str]:
    """
    Classify a market for contrarian fear trading.

    Returns:
        "BET_YES"  — recovery/normalization market (we expect recovery)
        "BET_NO"   — crash continuation market (contrarian)
        None       — skip
    """
    title = (_market_attr(market, "question", "title") or "").lower()
    volume = float(_market_attr(market, "volume", "total_volume") or 100)  # default 100 if missing
    status = _market_attr(market, "status") or "open"

    if volume < MIN_MARKET_VOLUME:
        return None
    if status not in (None, "open", "active"):
        return None

    yes_prob = _get_yes_prob(market)
    if yes_prob is None:
        return None

    is_crypto = any(kw in title for kw in ["bitcoin", "btc", "crypto", "ethereum", "eth", "sol"])

    # "Up or Down" style directional market — during extreme fear, YES = bullish = contrarian play
    if is_crypto and "up" in title and "down" in title:
        if MIN_YES_PROB <= yes_prob <= 0.60:
            return "BET_YES"

    # Recovery / bullish markets — bet YES
    recovery_signals = any(kw in title for kw in [
        "recover", "above", "exceed", "reach", "bullish",
        "higher", "rise", "hit", "surpass", "outperform",
    ])
    # Crash continuation — bet NO (we're contrarian)
    crash_signals = any(kw in title for kw in CRASH_KEYWORDS)

    if recovery_signals and not crash_signals:
        if MIN_YES_PROB <= yes_prob <= MAX_YES_PROB:
            return "BET_YES"
    elif crash_signals and not recovery_signals:
        if yes_prob >= 0.50:
            return "BET_NO"

    # Any crypto market priced pessimistically (YES < 40%) — contrarian YES bet
    if is_crypto and yes_prob < 0.40:
        return "BET_YES"

    return None


# ---------------------------------------------------------------------------
# Trade execution
# ---------------------------------------------------------------------------

def execute_fear_trades(
    fg_value: int,
    client: Any,
    *,
    dry_run: bool = True,
    bet_amount: float = BET_PER_MARKET,
    max_bets: int = MAX_BETS_PER_RUN,
) -> list[dict[str, Any]]:
    """
    Find and execute contrarian Simmer bets during extreme fear.

    Args:
        fg_value: Current Fear & Greed index value
        client:   Simmer SDK client
        dry_run:  If True, log but don't submit trades
        bet_amount: $SIM per bet
        max_bets:   Max number of markets to bet on

    Returns:
        List of executed (or simulated) trade records
    """
    markets = find_fear_markets(client)
    logger.info("Simmer: %d candidate markets found", len(markets))

    trades = []
    bets_placed = 0

    # Sort by divergence desc (highest edge first), fallback to order received
    markets.sort(
        key=lambda m: float(_market_attr(m, "divergence") or 0),
        reverse=True,
    )

    for market in markets:
        if bets_placed >= max_bets:
            break

        action = classify_market(market)
        if action is None:
            continue

        market_id = _market_attr(market, "market_id", "id")
        title = _market_attr(market, "question", "title") or "Unknown"
        yes_prob = _get_yes_prob(market) or 0.0
        volume = float(_market_attr(market, "volume", "total_volume") or 0)

        side = "yes" if action == "BET_YES" else "no"
        reasoning = (
            f"Contrarian fear trade: F&G={fg_value} (Extreme Fear). "
            f"{'Recovery expected — betting YES on upside.' if side == 'yes' else 'Crash continuation unlikely — betting NO.'} "
            f"Market: {title[:80]}"
        )

        trade_record = {
            "market_id": market_id,
            "title": title[:80],
            "side": side,
            "amount": bet_amount,
            "yes_prob_at_entry": yes_prob,
            "volume": volume,
            "fg_at_entry": fg_value,
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "result": None,
        }

        if dry_run:
            logger.info(
                "[DRY RUN] Would bet $%.0f %s on '%s' (prob=%.2f, vol=%.0f)",
                bet_amount, side.upper(), title[:60], yes_prob, volume,
            )
            trade_record["result"] = "DRY_RUN"
        else:
            try:
                result = client.trade(
                    market_id=market_id,
                    side=side,
                    amount=bet_amount,
                    source="fear-harvester",
                    reasoning=reasoning,
                )
                trade_record["result"] = result
                logger.info(
                    "✅ Simmer trade: $%.0f %s on '%s' — %s",
                    bet_amount, side.upper(), title[:60], result,
                )
            except Exception as e:
                logger.error("Simmer trade failed for %s: %s", market_id, e)
                trade_record["result"] = f"ERROR: {e}"
                continue

        trades.append(trade_record)
        bets_placed += 1

    return trades


# ---------------------------------------------------------------------------
# Briefing (heartbeat)
# ---------------------------------------------------------------------------

def get_briefing(client: Any, since_hours: int = 4) -> dict[str, Any]:
    """
    Build a briefing dict from available Simmer SDK methods.

    Returns normalised dict with portfolio, positions, pnl.
    """
    try:
        portfolio = client.get_portfolio() or {}
        positions = client.get_positions() or []
        pnl = client.get_total_pnl()
        return {
            "portfolio": portfolio,
            "positions": positions,
            "total_pnl": pnl,
        }
    except Exception as e:
        logger.warning("Simmer briefing failed: %s", e)
        return {}


def format_briefing_summary(briefing: dict[str, Any]) -> str:
    """Format Simmer state as a human-readable summary string."""
    if not briefing:
        return "Simmer: briefing unavailable"

    portfolio = briefing.get("portfolio") or {}
    balance = portfolio.get("balance_usdc", portfolio.get("sim_balance", "?"))
    exposure = portfolio.get("total_exposure", 0)
    n_pos = portfolio.get("positions_count", len(briefing.get("positions") or []))
    pnl = briefing.get("total_pnl", portfolio.get("pnl_total", 0)) or 0
    pnl_icon = "📈" if pnl >= 0 else "📉"

    lines = [
        f"💹 Simmer: ${balance:.2f} USDC | {n_pos} position(s) | "
        f"Exposure ${exposure:.2f} | {pnl_icon} P&L ${pnl:+.2f}"
    ]

    positions = briefing.get("positions") or []
    if positions:
        for pos in positions[:2]:  # Show top 2
            title = _market_attr(pos, "question", "title", "market_id") or "?"
            shares_yes = float(_market_attr(pos, "shares_yes") or 0)
            shares_no = float(_market_attr(pos, "shares_no") or 0)
            side = "YES" if shares_yes > shares_no else "NO"
            pnl = float(_market_attr(pos, "pnl") or 0)
            lines.append(f"  • {side} {str(title)[:50]} (P&L ${pnl:+.2f})")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Simmer crypto fear trades")
    parser.add_argument("--fg", type=int, required=True, help="Current Fear & Greed value")
    parser.add_argument("--live", action="store_true", help="Execute real trades (virtual $SIM)")
    parser.add_argument("--briefing", action="store_true", help="Just show briefing, no trades")
    args = parser.parse_args()

    client = _load_client()

    if args.briefing:
        b = get_briefing(client)
        print(format_briefing_summary(b))
    else:
        trades = execute_fear_trades(args.fg, client, dry_run=not args.live)
        print(json.dumps(trades, indent=2, default=str))
