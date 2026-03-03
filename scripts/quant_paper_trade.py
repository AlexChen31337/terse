"""
Quant Paper Trading Monitor — AlphaStrike V2
Runs every 4h, generates signals, logs paper trades, reports to Alex.
"""
from __future__ import annotations

import json
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
PAPER_BOOK = WORKSPACE / "memory" / "paper-trades.json"
MIN_CONFIDENCE = 0.55


def load_book() -> dict:
    if PAPER_BOOK.exists():
        return json.loads(PAPER_BOOK.read_text())
    return {"positions": {}, "closed": [], "equity_curve": [], "starting_equity": 1000.0}


def save_book(book: dict):
    PAPER_BOOK.write_text(json.dumps(book, indent=2, default=str))


def get_signals() -> list[dict]:
    result = subprocess.run(
        ["uv", "run", "python",
         str(WORKSPACE / "skills/alphastrike/scripts/alphastrike_signal.py"),
         "--assets", "BTC", "ETH", "SOL", "--output", "json"],
        capture_output=True, text=True, cwd=str(WORKSPACE)
    )
    if result.returncode != 0:
        print(f"Signal error: {result.stderr[:200]}", file=sys.stderr)
        return []
    data = json.loads(result.stdout)
    return data.get("signals", [])


def compute_equity(book: dict) -> float:
    # Simplified: equity = starting + sum of closed P&L
    eq = book["starting_equity"]
    for t in book["closed"]:
        eq += t.get("pnl_usd", 0)
    return round(eq, 2)


def process_signals(signals: list[dict], book: dict) -> list[str]:
    messages = []
    now = datetime.now(timezone.utc).isoformat()
    position_size_usd = 50.0  # $50 per paper trade

    for sig in signals:
        sym = sig["symbol"]
        signal = sig["signal"]  # LONG / SHORT / NEUTRAL
        conf = sig["confidence"]
        price = sig["price"]
        reasoning = sig.get("reasoning", "")

        existing = book["positions"].get(sym)

        # --- Exit logic: close if signal flips or new strong signal ---
        if existing:
            direction = existing["direction"]
            entry_price = existing["entry_price"]
            pnl_pct = ((price - entry_price) / entry_price) * (1 if direction == "LONG" else -1)
            pnl_usd = round(pnl_pct * position_size_usd, 2)

            should_close = (
                (direction == "LONG" and signal == "SHORT") or
                (direction == "SHORT" and signal == "LONG") or
                (signal == "NEUTRAL" and conf > 0.6) or
                pnl_pct <= -0.05 or  # stop-loss 5%
                pnl_pct >= 0.10      # take-profit 10%
            )

            if should_close:
                reason = "signal_flip" if signal != direction else ("stop_loss" if pnl_pct <= -0.05 else "take_profit")
                closed = {**existing, "exit_price": price, "exit_time": now,
                          "pnl_usd": pnl_usd, "pnl_pct": round(pnl_pct * 100, 2), "exit_reason": reason}
                book["closed"].append(closed)
                del book["positions"][sym]
                emoji = "✅" if pnl_usd >= 0 else "❌"
                messages.append(
                    f"{emoji} CLOSE {sym} {direction} @ ${price:,.2f} | "
                    f"P&L: ${pnl_usd:+.2f} ({pnl_pct*100:+.1f}%) [{reason}]"
                )
                existing = None  # fall through to re-enter if signal strong

        # --- Entry logic ---
        if not existing and signal in ("LONG", "SHORT") and conf >= MIN_CONFIDENCE:
            book["positions"][sym] = {
                "symbol": sym, "direction": signal,
                "entry_price": price, "entry_time": now,
                "confidence": conf, "size_usd": position_size_usd,
                "reasoning": reasoning,
            }
            messages.append(
                f"📈 OPEN {sym} {signal} @ ${price:,.2f} | "
                f"conf={conf:.0%} | {reasoning[:80]}"
            )
        elif not existing:
            messages.append(
                f"⏸  {sym} {signal} conf={conf:.0%} — below threshold, no trade"
            )

    return messages


def main():
    book = load_book()
    signals = get_signals()

    if not signals:
        print("[Quant] Failed to get signals")
        return

    msgs = process_signals(signals, book)

    # Log equity snapshot
    equity = compute_equity(book)
    book["equity_curve"].append({"time": datetime.now(timezone.utc).isoformat(), "equity": equity})
    save_book(book)

    # Build report
    open_pos = book["positions"]
    closed_count = len(book["closed"])
    wins = sum(1 for t in book["closed"] if t.get("pnl_usd", 0) > 0)
    total_pnl = sum(t.get("pnl_usd", 0) for t in book["closed"])
    win_rate = (wins / closed_count * 100) if closed_count else 0

    report_lines = [
        "📊 **[Quant] AlphaStrike V2 Paper Trading Update**",
        "",
        *msgs,
        "",
        f"**Open positions:** {len(open_pos)} | " +
        (", ".join(f"{s} {p['direction']} @ ${p['entry_price']:,.2f}" for s, p in open_pos.items()) or "none"),
        f"**Closed trades:** {closed_count} | Win rate: {win_rate:.0f}% | Total P&L: ${total_pnl:+.2f}",
        f"**Paper equity:** ${equity:,.2f} (started $1,000)",
    ]

    report = "\n".join(report_lines)
    print(report)

    # Report to Alex's main session
    try:
        import os
        sys.path.insert(0, str(WORKSPACE))
        # Write to a file for Alex to pick up via heartbeat
        report_file = WORKSPACE / "memory" / "quant-latest-report.md"
        report_file.write_text(f"# Quant Report\n_{datetime.now(timezone.utc).isoformat()}_\n\n{report}\n")
    except Exception as e:
        print(f"Report write error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
