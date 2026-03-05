"""
Quant Paper Trading Monitor — AlphaStrike V2 (Real Engine)
Runs every 4h via cron. Uses the actual V2 stacking ensemble + signal processor.

Architecture compliance:
  - V2FeaturePipeline (25 features, named + bounded)
  - StackingEnsemble (LightGBM + Ridge + RollingStats + meta-learner)
    → close_prices passed to predict() so RollingStats returns real values
  - UnifiedRegimeDetector (4-state: TREND_UP/DOWN/RANGE/CHAOS)
  - SignalProcessor (6 PRD filters: RSI, ADX, regime, agreement, breakeven, cost)
  - Reports to Alex main session via memory file
"""
from __future__ import annotations

import asyncio
import json
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

WORKSPACE = Path(__file__).parent.parent
V2_DIR    = WORKSPACE / "alphastrike-v2"
PAPER_BOOK = WORKSPACE / "memory" / "paper-trades.json"
MIN_CONFIDENCE = 0.30   # V2 default from ModelConfig (was 0.40 on wrong script)

# Ensure alphastrike-v2 package is importable
sys.path.insert(0, str(V2_DIR))


# ── V2 engine imports ─────────────────────────────────────────────────────────

from alphastrike.exchange.hyperliquid import HyperliquidAdapter  # noqa: E402
from alphastrike.features.pipeline import V2FeaturePipeline       # noqa: E402
from alphastrike.strategy.regime import UnifiedRegimeDetector      # noqa: E402
from alphastrike.strategy.signals import SignalProcessor           # noqa: E402


# ── Paper book helpers ────────────────────────────────────────────────────────

def load_book() -> dict:
    if PAPER_BOOK.exists():
        return json.loads(PAPER_BOOK.read_text())
    return {"positions": {}, "closed": [], "equity_curve": [], "starting_equity": 1000.0}


def save_book(book: dict) -> None:
    PAPER_BOOK.write_text(json.dumps(book, indent=2, default=str))


def compute_equity(book: dict) -> float:
    eq = book["starting_equity"]
    for t in book["closed"]:
        eq += t.get("pnl_usd", 0)
    return round(eq, 2)


# ── Signal generation via real V2 engine ─────────────────────────────────────

async def get_v2_signals() -> list[dict] | None:
    """
    Run the full V2 pipeline per asset and return structured signal dicts.
    Passes close_prices to ensemble.predict() so RollingStatsModel works.
    """
    try:
        adapter  = HyperliquidAdapter()
        pipeline = V2FeaturePipeline()
        regime_detector = UnifiedRegimeDetector()
        processor = SignalProcessor()

        # BTC candles fetched first — needed for cross-asset correlation feature
        btc_candles = await adapter.get_candles(symbol="BTC", interval="1h", limit=200)
        btc_closes  = np.array([float(c.close) for c in btc_candles])

        signals = []

        for asset in ["BTC", "ETH", "SOL"]:
            model_path = V2_DIR / f"models/{asset.lower()}_ensemble_full.pkl"
            if not model_path.exists():
                print(f"[V2] {asset}: model not found at {model_path}", file=sys.stderr)
                continue

            with open(model_path, "rb") as f:
                ensemble = pickle.load(f)

            candles = await adapter.get_candles(symbol=asset, interval="1h", limit=200)
            if not candles or len(candles) < 100:
                print(f"[V2] {asset}: insufficient candles ({len(candles)})", file=sys.stderr)
                continue

            closes  = np.array([float(c.close) for c in candles])
            highs   = np.array([float(c.high)  for c in candles])
            lows    = np.array([float(c.low)   for c in candles])
            volumes = np.array([float(c.volume) for c in candles])

            # 25-feature pipeline
            features = pipeline.calculate(
                closes, highs, lows, volumes,
                btc_close=btc_closes if asset != "BTC" else None,
                timestamp=datetime.now(timezone.utc),
            )

            # 4-state regime (hysteresis-guarded)
            regime_state = regime_detector.update(
                close=closes[-50:], high=highs[-50:], low=lows[-50:]
            )

            # ML ensemble — pass close_prices so RollingStats gets real data
            feat_keys = sorted(features)
            X = np.array([[features[k] for k in feat_keys]])
            prediction = ensemble.predict(X, close_prices=closes)

            # 6-filter signal processor (RSI, ADX, regime, agreement, breakeven, cost)
            result = processor.process(prediction, features, regime_state)

            reasoning_parts = [
                f"regime={regime_state.regime.value}(ADX={regime_state.adx:.0f})",
                f"ML_ret={prediction.predicted_return:.4%}",
                f"conf={prediction.confidence:.0%}",
                f"scale={result.position_scale:.2f}",
            ]
            if result.block_reason:
                reasoning_parts.append(f"blocked={result.block_reason}")
            if result.filters_failed:
                reasoning_parts.append(f"failed={result.filters_failed}")

            signals.append({
                "symbol": asset,
                "signal": result.signal,           # LONG / SHORT / HOLD
                "confidence": result.position_scale * prediction.confidence,
                "price": float(closes[-1]),
                "reasoning": "; ".join(reasoning_parts),
                # diagnostic extras
                "_regime": regime_state.regime.value,
                "_ml_signal": prediction.signal,
                "_ml_ret": prediction.predicted_return,
                "_ml_conf": prediction.confidence,
                "_base_preds": prediction.base_predictions,
                "_filters_passed": result.filters_passed,
                "_filters_failed": result.filters_failed,
                "_block_reason": result.block_reason,
                "_position_scale": result.position_scale,
            })

        await adapter._close_session()
        return signals

    except Exception as e:
        import traceback
        print(f"[V2] Signal engine error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return None


# ── Paper trading logic ───────────────────────────────────────────────────────

def process_signals(signals: list[dict], book: dict) -> list[str]:
    messages = []
    now = datetime.now(timezone.utc).isoformat()
    position_size_usd = 50.0

    for sig in signals:
        sym      = sig["symbol"]
        signal   = sig["signal"]   # LONG / SHORT / HOLD
        conf     = sig["confidence"]
        price    = sig["price"]
        reasoning = sig.get("reasoning", "")
        existing = book["positions"].get(sym)

        # --- Exit check ---
        if existing:
            direction   = existing["direction"]
            entry_price = existing["entry_price"]
            pnl_pct     = ((price - entry_price) / entry_price) * (1 if direction == "LONG" else -1)
            pnl_usd     = round(pnl_pct * position_size_usd, 2)

            should_close = (
                (direction == "LONG"  and signal == "SHORT") or
                (direction == "SHORT" and signal == "LONG")  or
                (signal == "HOLD"     and conf > 0.5)        or
                pnl_pct <= -0.05 or   # 5% stop-loss
                pnl_pct >=  0.10      # 10% take-profit
            )

            if should_close:
                reason = (
                    "signal_flip" if signal in ("LONG", "SHORT") and signal != direction
                    else "stop_loss" if pnl_pct <= -0.05
                    else "take_profit" if pnl_pct >= 0.10
                    else "flat_signal"
                )
                closed = {
                    **existing,
                    "exit_price": price, "exit_time": now,
                    "pnl_usd": pnl_usd, "pnl_pct": round(pnl_pct * 100, 2),
                    "exit_reason": reason,
                }
                book["closed"].append(closed)
                del book["positions"][sym]
                emoji = "✅" if pnl_usd >= 0 else "❌"
                messages.append(
                    f"{emoji} CLOSE {sym} {direction} @ ${price:,.2f} | "
                    f"P&L: ${pnl_usd:+.2f} ({pnl_pct*100:+.1f}%) [{reason}]"
                )
                existing = None

        # --- Entry check ---
        if not existing and signal in ("LONG", "SHORT") and conf >= MIN_CONFIDENCE:
            book["positions"][sym] = {
                "symbol": sym, "direction": signal,
                "entry_price": price, "entry_time": now,
                "confidence": conf, "size_usd": position_size_usd,
                "reasoning": reasoning,
            }
            messages.append(
                f"📈 OPEN {sym} {signal} @ ${price:,.2f} | "
                f"conf={conf:.0%} | {reasoning[:100]}"
            )
        elif not existing:
            # Show why: block reason or low confidence
            block = sig.get("_block_reason") or sig.get("_filters_failed") or "below_threshold"
            messages.append(f"⏸  {sym} {signal} conf={conf:.0%} — {block}")

    return messages


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    book    = load_book()
    signals = asyncio.run(get_v2_signals())

    if signals is None:
        print("[Quant] Failed to get signals from V2 engine")
        return

    msgs   = process_signals(signals, book)
    equity = compute_equity(book)
    book["equity_curve"].append({
        "time": datetime.now(timezone.utc).isoformat(),
        "equity": equity,
    })
    save_book(book)

    # Build report
    open_pos     = book["positions"]
    closed_count = len(book["closed"])
    wins         = sum(1 for t in book["closed"] if t.get("pnl_usd", 0) > 0)
    total_pnl    = sum(t.get("pnl_usd", 0) for t in book["closed"])
    win_rate     = (wins / closed_count * 100) if closed_count else 0

    report_lines = [
        "📊 **[Quant] AlphaStrike V2 Paper Trading Update**",
        "",
        *msgs,
        "",
        f"**Open positions:** {len(open_pos)} | " +
        (", ".join(
            f"{s} {p['direction']} @ ${p['entry_price']:,.2f}"
            for s, p in open_pos.items()
        ) or "none"),
        f"**Closed trades:** {closed_count} | Win rate: {win_rate:.0f}% | Total P&L: ${total_pnl:+.2f}",
        f"**Paper equity:** ${equity:,.2f} (started $1,000)",
    ]

    report = "\n".join(report_lines)
    print(report)

    # Persist for Alex heartbeat pickup
    report_file = WORKSPACE / "memory" / "quant-latest-report.md"
    report_file.write_text(
        f"# Quant Report\n_{datetime.now(timezone.utc).isoformat()}_\n\n{report}\n"
    )


if __name__ == "__main__":
    main()
