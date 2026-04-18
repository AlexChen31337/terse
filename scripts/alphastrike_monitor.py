#!/usr/bin/env python3
"""
AlphaStrike V2 monitor — watches the live log and tmux session.
Detects: trades, balance changes, crashes, errors.
Outputs structured status for the cron agent to act on.
"""
import os
import re
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

LOG_PATH = "/media/DATA/tmp/alphastrike-live.log"
STATE_FILE = Path.home() / "clawd/memory/alphastrike-state.json"
SYSTEMD_SERVICE = "alphastrike.service"


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_trades": 0, "last_balance": 10000.0, "last_cycle": 0, "last_positions": 0, "alerts_sent": []}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def service_alive():
    """Check if alphastrike systemd user service is active."""
    try:
        uid = os.getuid()
        env = {**os.environ, "XDG_RUNTIME_DIR": f"/run/user/{uid}"}
        r = subprocess.run(
            ["systemctl", "--user", "is-active", SYSTEMD_SERVICE],
            capture_output=True, text=True, timeout=5, env=env
        )
        return r.stdout.strip() == "active"
    except Exception:
        return False


def parse_log():
    """Parse last 200 lines of log for key metrics."""
    try:
        # Tail for recent metrics
        result = subprocess.run(["tail", "-200", LOG_PATH],
                                capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().split("\n")
        # Check full log for startup warnings (once at boot)
        grep_result = subprocess.run(
            ["grep", "-c", "No models directory found", LOG_PATH],
            capture_output=True, text=True, timeout=5)
        no_models = int(grep_result.stdout.strip() or "0") > 0
    except Exception:
        return None

    latest = {"cycle": 0, "balance": None, "positions": 0, "trades": 0,
              "errors": [], "warnings": [], "no_models": no_models, "regime": None}

    for line in lines:
        # New format: [Cycle N] Balance: $X | Positions: Y | Entries: Z | Skips: W
        m = re.search(r'\[Cycle (\d+)\] Balance: \$([0-9,.]+) \| Positions: (\d+) \| Entries: (\d+) \| Skips: (\d+)', line)
        if m:
            c, bal, pos, entries, skips = int(m.group(1)), float(m.group(2).replace(',','')), int(m.group(3)), int(m.group(4)), int(m.group(5))
            if c > latest["cycle"]:
                latest.update({"cycle": c, "balance": bal, "positions": pos,
                                "trades": entries, "skips": skips})
            continue
        # Legacy format fallback: [Cycle N] Balance: $X | Positions: Y | Trades: Z
        m = re.search(r'\[Cycle (\d+)\] Balance: \$([0-9,.]+) \| Positions: (\d+) \| Trades: (\d+)', line)
        if m:
            c, bal, pos, trades = int(m.group(1)), float(m.group(2).replace(',','')), int(m.group(3)), int(m.group(4))
            if c > latest["cycle"]:
                latest.update({"cycle": c, "balance": bal, "positions": pos, "trades": trades})

        if "ERROR" in line and "alphastrike" in line.lower():
            latest["errors"].append(line[-150:])

        if "WARNING" in line and "No models" not in line:
            latest["warnings"].append(line[-120:])

        # Regime changes
        m2 = re.search(r'Regime change: (\w+) → (\w+)', line)
        if m2:
            latest["regime"] = f"{m2.group(1)} → {m2.group(2)}"

        # Trade entries/exits (future — when models are trained)
        if any(k in line for k in ["ENTER", "EXIT", "LONG", "SHORT", "filled", "closed", "PnL", "profit"]):
            latest.setdefault("trade_lines", []).append(line[-200:])

    return latest


def main():
    state = load_state()
    alive = service_alive()
    data = parse_log()
    alerts = []

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── 1. Service down ────────────────────────────────────────────────────
    if not alive:
        alerts.append(f"🚨 CRASH: AlphaStrike systemd service '{SYSTEMD_SERVICE}' is DOWN. Check: journalctl --user -u alphastrike -n 20")

    # ── 2. No models warning (once per session) ────────────────────────────
    if data and data["no_models"] and "no_models_warned" not in state.get("alerts_sent", []):
        alerts.append(
            "⚠️ NO MODELS: AlphaStrike started without trained ML models — "
            "no trades will fire until models are trained. Run training first!"
        )
        state.setdefault("alerts_sent", []).append("no_models_warned")

    if data:
        cycle = data["cycle"]
        balance = data["balance"]
        trades = data["trades"]
        positions = data["positions"]

        # ── 3. New ENTRY fired (not skips) ────────────────────────────────
        if trades > state["last_trades"]:
            new = trades - state["last_trades"]
            skips = data.get("skips", 0)
            alerts.append(
                f"💰 ENTRY FIRED: {new} new position(s) opened! "
                f"Balance: ${balance:,.2f} | Total entries: {trades} | Positions open: {positions}"
            )
            if data.get("trade_lines"):
                for tl in data["trade_lines"][-3:]:
                    alerts.append(f"  └ {tl}")

        # ── 4. Balance change > $10 ────────────────────────────────────────
        bal_diff = balance - state["last_balance"] if balance else 0
        if abs(bal_diff) >= 10 and trades > 0:
            sign = "📈" if bal_diff > 0 else "📉"
            pct = (bal_diff / state["last_balance"]) * 100
            alerts.append(
                f"{sign} P&L MOVE: ${bal_diff:+.2f} ({pct:+.1f}%) "
                f"| Balance now: ${balance:,.2f}"
            )

        # ── 5. Position opened/closed ──────────────────────────────────────
        if positions != state["last_positions"] and state["last_positions"] is not None:
            if positions > state["last_positions"]:
                alerts.append(f"📌 POSITION OPENED: {positions} active position(s)")
            else:
                alerts.append(f"✅ POSITION CLOSED: {positions} remaining open")

        # ── 6. Recent errors ───────────────────────────────────────────────
        for err in data["errors"][-2:]:
            if err not in state.get("seen_errors", []):
                alerts.append(f"❌ ERROR: {err}")
                state.setdefault("seen_errors", []).append(err)

        # ── Update state ───────────────────────────────────────────────────
        state.update({
            "last_trades": trades,
            "last_balance": balance or state["last_balance"],
            "last_cycle": cycle,
            "last_positions": positions,
            "last_check": ts,
        })

    save_state(state)

    # ── Output ─────────────────────────────────────────────────────────────
    if alerts:
        print("ALERT")
        for a in alerts:
            print(a)
    else:
        # Status line for periodic summary (every ~2h in cron)
        if data:
            regime = data.get("regime") or "unknown"
            print(f"OK | Cycle {data['cycle']} | Balance ${data['balance']:,.2f} | "
                  f"Entries {data['trades']} | Skips {data.get('skips',0)} | "
                  f"Positions {data['positions']} | Session {'✅' if alive else '❌'}")
        else:
            print("OK | no data")


if __name__ == "__main__":
    main()
