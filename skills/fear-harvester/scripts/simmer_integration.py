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

v2 changes:
  - Fixed volume filter: volume=0 → skip (don't default to 100)
  - Added market duration filter: skip <1h and 5/15-min candle markets
  - Added position deduplication: state file tracks open market IDs
  - Added max total open positions cap (default 5)
  - Smarter title scoring: prefer weekly/monthly resolution markets
"""
from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

# Add Simmer SDK to path
SIMMER_VENV = Path("/home/bowen/clawd/skills/simmer/.venv/lib/python3.11/site-packages")
if str(SIMMER_VENV) not in sys.path:
    sys.path.insert(0, str(SIMMER_VENV))

SIMMER_CREDS_PATH = Path.home() / ".config/simmer/credentials.json"
SIMMER_STATE_PATH = Path(__file__).parent.parent / "data" / "simmer_state.json"

logger = logging.getLogger("fear-harvester.simmer")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BET_PER_MARKET = 5.0        # USDC per bet (real money — conservative)
MAX_BETS_PER_RUN = 2        # Max new bets per F&G check
MAX_TOTAL_POSITIONS = 5     # Hard cap: don't open if already ≥ this many open
MIN_MARKET_VOLUME = 100.0   # Skip thin markets (must have real volume)
MIN_YES_PROB = 0.25         # Don't bet YES if probability already > 75% (low edge)
MAX_YES_PROB = 0.75
USDC_ONLY = True            # Only trade on USDC markets (no $SIM)

# Patterns for short-term candle markets to EXCLUDE (these are coin flips)
SHORT_TERM_CANDLE_PATTERNS = [
    r"\d+:\d+\s*(AM|PM)\s*[-–]\s*\d+:\d+\s*(AM|PM)",  # "8:00AM-8:15AM" style
    r"(Up or Down|up or down).*(ET|UTC|GMT)",            # directional with timezone
    r"\d+\s*min(ute)?",                                  # "15 minute" markets
]

# Keywords for finding relevant markets
RECOVERY_KEYWORDS = [
    "bitcoin", "btc", "crypto", "fear greed", "cryptocurrency",
    "ethereum", "eth", "bull", "recovery",
]
CRASH_KEYWORDS = ["crash", "bear", "below", "collapse", "dump"]

# Preferred resolution horizon keywords (score boost)
LONG_HORIZON_KEYWORDS = [
    "end of", "by end", "week", "month", "march", "april", "may",
    "q1", "q2", "2026", "year",
]


# ---------------------------------------------------------------------------
# State management (deduplication)
# ---------------------------------------------------------------------------

def _load_simmer_state() -> dict[str, Any]:
    """Load open position tracking state."""
    try:
        if SIMMER_STATE_PATH.exists():
            return json.loads(SIMMER_STATE_PATH.read_text())
    except Exception:
        pass
    return {"open_market_ids": [], "last_updated": None}


def _save_simmer_state(state: dict[str, Any]) -> None:
    """Persist open position tracking state."""
    SIMMER_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    SIMMER_STATE_PATH.write_text(json.dumps(state, indent=2))


def _sync_open_positions(client: Any, state: dict[str, Any]) -> dict[str, Any]:
    """
    Refresh open_market_ids from live Simmer positions.
    Removes markets we've exited (resolved/closed).
    """
    try:
        live_positions = client.get_positions() or []
        live_ids = set()
        for pos in live_positions:
            mid = _market_attr(pos, "market_id", "id")
            if mid:
                # Only keep if position has nonzero shares
                shares_yes = float(_market_attr(pos, "shares_yes") or 0)
                shares_no = float(_market_attr(pos, "shares_no") or 0)
                if shares_yes > 0 or shares_no > 0:
                    live_ids.add(str(mid))

        state["open_market_ids"] = list(live_ids)
        logger.info("Simmer: %d open positions synced from API", len(live_ids))
    except Exception as e:
        logger.warning("Simmer: failed to sync positions: %s — using cached state", e)

    return state


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
# Market filtering
# ---------------------------------------------------------------------------

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
    for key in ("current_probability", "yes_price", "yes_prob", "probability", "external_price_yes"):
        val = _market_attr(market, key)
        if val is not None:
            try:
                p = float(val)
                return p if p <= 1.0 else p / 100.0
            except (TypeError, ValueError):
                continue
    return None


def _is_short_term_candle(title: str) -> bool:
    """
    Return True if this is a short-term (5-60min) directional candle market.
    These are coin flips — no edge from fear/greed signals at 5-min resolution.
    """
    for pattern in SHORT_TERM_CANDLE_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return True
    return False


def _has_real_volume(market: Any) -> bool:
    """
    Return True only if market has explicitly nonzero volume.
    volume=0 or volume=None → thin/inactive → skip.
    """
    vol_raw = _market_attr(market, "volume", "total_volume")
    if vol_raw is None:
        return False  # Unknown volume → skip conservatively
    try:
        return float(vol_raw) >= MIN_MARKET_VOLUME
    except (TypeError, ValueError):
        return False


def _long_horizon_score(title: str) -> int:
    """Score [0–3] boost for markets resolving over longer horizons."""
    title_lower = title.lower()
    return sum(1 for kw in LONG_HORIZON_KEYWORDS if kw in title_lower)


def find_fear_markets(client: Any) -> list[Any]:
    """
    Find crypto markets relevant to a fear-based contrarian trade.
    Filters out candle markets and low-volume markets.
    Returns markets sorted by long-horizon score + volume desc.
    """
    candidates = []
    seen_ids: set[str] = set()

    for keyword in ["bitcoin", "crypto", "btc", "fear", "cryptocurrency"]:
        try:
            markets = client.find_markets(keyword)
            for m in (markets or []):
                mid = str(_market_attr(m, "market_id", "id") or id(m))
                if mid in seen_ids:
                    continue
                seen_ids.add(mid)

                title = (_market_attr(m, "question", "title") or "").strip()

                # Hard filter: skip 5-60min candle markets
                if _is_short_term_candle(title):
                    logger.debug("Simmer: skipping candle market — %s", title[:60])
                    continue

                # Hard filter: must have real volume
                if not _has_real_volume(m):
                    logger.debug("Simmer: skipping zero-volume market — %s", title[:60])
                    continue

                # Hard filter: USDC only (no $SIM paper markets)
                if USDC_ONLY:
                    currency = str(_market_attr(m, "currency") or "").upper()
                    if currency and currency != "USDC":
                        logger.debug("Simmer: skipping non-USDC market — %s (%s)", title[:60], currency)
                        continue

                candidates.append(m)
        except Exception as e:
            logger.warning("Simmer market search failed for '%s': %s", keyword, e)

    # Sort: long-horizon score (desc), then volume (desc)
    candidates.sort(
        key=lambda m: (
            _long_horizon_score(_market_attr(m, "question", "title") or ""),
            float(_market_attr(m, "volume", "total_volume") or 0),
        ),
        reverse=True,
    )

    logger.info("Simmer: %d qualifying markets after filtering", len(candidates))
    return candidates


def classify_market(market: Any) -> Optional[str]:
    """
    Classify a market for contrarian fear trading.

    Returns:
        "BET_YES"  — recovery/normalization market (we expect recovery)
        "BET_NO"   — crash continuation market (contrarian)
        None       — skip
    """
    title = (_market_attr(market, "question", "title") or "").lower()
    status = _market_attr(market, "status") or "open"

    if status not in (None, "open", "active"):
        return None

    yes_prob = _get_yes_prob(market)
    if yes_prob is None:
        return None

    is_crypto = any(kw in title for kw in ["bitcoin", "btc", "crypto", "ethereum", "eth", "sol"])

    # Recovery / bullish markets — bet YES
    recovery_signals = any(kw in title for kw in [
        "recover", "above", "exceed", "reach", "bullish",
        "higher", "rise", "hit", "surpass", "outperform",
    ])
    # Crash continuation — bet NO (contrarian)
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
    max_total_positions: int = MAX_TOTAL_POSITIONS,
) -> list[dict[str, Any]]:
    """
    Find and execute contrarian Simmer bets during extreme fear.

    v2: deduplication (no re-betting same market), total position cap,
    no short-term candle markets, real volume filter.
    """
    # Sync open positions from API
    state = _load_simmer_state()
    state = _sync_open_positions(client, state)
    open_ids: set[str] = set(state.get("open_market_ids", []))

    # Cap: don't open more if already at limit
    if len(open_ids) >= max_total_positions:
        logger.info(
            "Simmer: already at max positions (%d/%d) — skipping this run",
            len(open_ids), max_total_positions,
        )
        _save_simmer_state(state)
        return []

    markets = find_fear_markets(client)
    remaining_slots = max_total_positions - len(open_ids)
    effective_max = min(max_bets, remaining_slots)

    trades = []
    bets_placed = 0

    for market in markets:
        if bets_placed >= effective_max:
            break

        action = classify_market(market)
        if action is None:
            continue

        market_id = str(_market_attr(market, "market_id", "id") or "")
        title = _market_attr(market, "question", "title") or "Unknown"

        # Deduplication: skip if we already have a position here
        if market_id in open_ids:
            logger.debug("Simmer: already have position in %s — skipping", title[:50])
            continue

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
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": dry_run,
            "result": None,
        }

        if dry_run:
            logger.info(
                "[DRY RUN] Would bet $%.0f %s on '%s' (prob=%.2f, vol=%.0f)",
                bet_amount, side.upper(), title[:60], yes_prob, volume,
            )
            trade_record["result"] = "DRY_RUN"
            open_ids.add(market_id)
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
                # Track as open position only if trade succeeded
                result_str = str(result)
                if "success=True" in result_str or "trade_id" in result_str.lower():
                    open_ids.add(market_id)
            except Exception as e:
                logger.error("Simmer trade failed for %s: %s", market_id, e)
                trade_record["result"] = f"ERROR: {e}"
                continue

        trades.append(trade_record)
        bets_placed += 1

    # Persist updated state
    state["open_market_ids"] = list(open_ids)
    _save_simmer_state(state)

    return trades


# ---------------------------------------------------------------------------
# TP/SL Position Management (v3)
# ---------------------------------------------------------------------------

# TP/SL thresholds (USDC — real money, conservative)
TP_PNL_PCT = 0.30        # Take profit at +30% PnL
SL_PNL_PCT = -0.15       # Stop loss at -15% PnL
TP_YES_PRICE = 0.85      # Take profit if YES price ≥ 0.85 (diminishing returns)
SL_YES_PRICE = 0.15      # Stop loss if YES price ≤ 0.15 (thesis broken)


def _is_candle_market(title: str) -> bool:
    """Return True if this is a short-term candle market (let it expire, don't manage)."""
    return _is_short_term_candle(title)


def _compute_pnl_pct(position: Any) -> Optional[float]:
    """Compute PnL as a percentage of cost basis."""
    pnl = float(_market_attr(position, "pnl") or 0)
    cost = float(_market_attr(position, "cost_basis", "avg_price", "entry_price") or 0)
    shares_yes = float(_market_attr(position, "shares_yes") or 0)
    shares_no = float(_market_attr(position, "shares_no") or 0)
    shares = max(shares_yes, shares_no)

    # Try cost basis first
    if cost > 0:
        return pnl / cost

    # Fallback: estimate cost from shares * entry price
    entry_price = float(_market_attr(position, "avg_price_yes", "avg_price_no", "entry_price") or 0)
    if entry_price > 0 and shares > 0:
        estimated_cost = shares * entry_price
        if estimated_cost > 0:
            return pnl / estimated_cost

    # Can't compute percentage without cost basis
    return None


def manage_positions(
    client: Any,
    *,
    dry_run: bool = True,
    tp_pnl_pct: float = TP_PNL_PCT,
    sl_pnl_pct: float = SL_PNL_PCT,
    tp_yes_price: float = TP_YES_PRICE,
    sl_yes_price: float = SL_YES_PRICE,
) -> list[dict[str, Any]]:
    """
    Scan open positions and apply TP/SL rules.

    Rules:
    1. Skip candle markets (5-15 min windows) — they resolve too fast
    2. Take profit: PnL% ≥ tp_pnl_pct OR current YES price ≥ tp_yes_price
    3. Stop loss: PnL% ≤ sl_pnl_pct OR current YES price ≤ sl_yes_price
    4. USDC positions: more conservative (TP +30%, SL -15%)

    Returns list of actions taken.
    """
    try:
        positions = client.get_positions() or []
    except Exception as e:
        logger.warning("Simmer: failed to get positions for TP/SL: %s", e)
        return []

    actions = []

    for pos in positions:
        market_id = str(_market_attr(pos, "market_id", "id") or "")
        title = str(_market_attr(pos, "question", "title") or "Unknown")
        currency = str(_market_attr(pos, "currency") or "$SIM")
        pnl = float(_market_attr(pos, "pnl") or 0)
        shares_yes = float(_market_attr(pos, "shares_yes") or 0)
        shares_no = float(_market_attr(pos, "shares_no") or 0)

        if shares_yes == 0 and shares_no == 0:
            continue  # No position

        # Skip candle markets — let them expire
        if _is_candle_market(title):
            continue

        # Only manage USDC positions (ignore $SIM legacy)
        if USDC_ONLY and currency.upper() != "USDC":
            continue

        # Current price
        yes_price = _get_yes_prob(pos)
        pnl_pct = _compute_pnl_pct(pos)

        # More conservative thresholds for real USDC
        is_real = currency.upper() == "USDC"
        eff_tp_pnl = 0.30 if is_real else tp_pnl_pct
        eff_sl_pnl = -0.15 if is_real else sl_pnl_pct

        side = "yes" if shares_yes > shares_no else "no"
        shares = max(shares_yes, shares_no)

        # Determine action
        action = None
        reason = None

        if pnl_pct is not None and pnl_pct >= eff_tp_pnl:
            action = "TAKE_PROFIT"
            reason = f"PnL {pnl_pct:+.0%} ≥ {eff_tp_pnl:+.0%} threshold"
        elif yes_price is not None and side == "yes" and yes_price >= tp_yes_price:
            action = "TAKE_PROFIT"
            reason = f"YES price {yes_price:.2f} ≥ {tp_yes_price} (diminishing returns)"
        elif pnl_pct is not None and pnl_pct <= eff_sl_pnl:
            action = "STOP_LOSS"
            reason = f"PnL {pnl_pct:+.0%} ≤ {eff_sl_pnl:+.0%} threshold"
        elif yes_price is not None and side == "yes" and yes_price <= sl_yes_price:
            action = "STOP_LOSS"
            reason = f"YES price {yes_price:.2f} ≤ {sl_yes_price} (thesis broken)"
        elif yes_price is not None and side == "no" and yes_price >= (1.0 - sl_yes_price):
            action = "STOP_LOSS"
            reason = f"YES price {yes_price:.2f} ≥ {1.0 - sl_yes_price:.2f} (NO thesis broken)"

        if action is None:
            continue

        # Execute exit
        exit_side = "no" if side == "yes" else "yes"  # Sell by buying opposite
        action_record = {
            "market_id": market_id,
            "title": title[:70],
            "action": action,
            "reason": reason,
            "side": side,
            "shares": shares,
            "pnl": pnl,
            "pnl_pct": f"{pnl_pct:+.1%}" if pnl_pct is not None else "?",
            "currency": currency,
            "dry_run": dry_run,
            "result": None,
        }

        if dry_run:
            logger.info(
                "[DRY RUN] %s: %s %.1f shares of '%s' (%s) — %s",
                action, side.upper(), shares, title[:50], reason,
                f"PnL ${pnl:+.2f}",
            )
            action_record["result"] = "DRY_RUN"
        else:
            try:
                result = client.trade(
                    market_id=market_id,
                    side=exit_side,
                    amount=shares,
                    source="fear-harvester-tpsl",
                    reasoning=f"{action}: {reason}",
                )
                action_record["result"] = result
                logger.info(
                    "✅ %s: Exited %s %.1f shares of '%s' — %s",
                    action, side.upper(), shares, title[:50], result,
                )
            except Exception as e:
                logger.error("TP/SL exit failed for %s: %s", market_id, e)
                action_record["result"] = f"ERROR: {e}"

        actions.append(action_record)

    if actions:
        logger.info("Simmer TP/SL: %d actions taken", len(actions))
    else:
        logger.debug("Simmer TP/SL: no actions needed")

    return actions


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
            pos_pnl = float(_market_attr(pos, "pnl") or 0)
            lines.append(f"  • {side} {str(title)[:50]} (P&L ${pos_pnl:+.2f})")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Simmer crypto fear trades")
    parser.add_argument("--fg", type=int, default=None, help="Current Fear & Greed value")
    parser.add_argument("--live", action="store_true", help="Execute real trades (virtual $SIM)")
    parser.add_argument("--briefing", action="store_true", help="Just show briefing, no trades")
    parser.add_argument("--manage", action="store_true", help="Run TP/SL position management")
    args = parser.parse_args()

    client = _load_client()

    if args.briefing:
        b = get_briefing(client)
        print(format_briefing_summary(b))
    elif args.manage:
        actions = manage_positions(client, dry_run=not args.live)
        print(json.dumps(actions, indent=2, default=str))
        if not actions:
            print("No TP/SL actions needed.")
    elif args.fg is not None:
        trades = execute_fear_trades(args.fg, client, dry_run=not args.live)
        print(json.dumps(trades, indent=2, default=str))
    else:
        parser.error("Specify --fg VALUE, --briefing, or --manage")
