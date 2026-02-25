#!/usr/bin/env python3
"""
Quant Daily Loop — runs every morning via cron
Scans AlphaStrike signals, checks Simmer briefing, monitors HL portfolio
Reports to Alex via sessions_send
"""

import json, os, sys, subprocess, requests
from datetime import datetime, timezone
from pathlib import Path

SKILL_DIR    = Path(__file__).parent
CONFIG_PATH  = SKILL_DIR / "risk_config.json"
HL_ADDRESS   = "0x64e830dd7af93431c898ea9e4c375c6706bd0fc5"
HL_API       = "https://api.hyperliquid.xyz/info"
ALPHASTRIKE  = Path.home() / "clawd/skills/alphastrike"
SIMMER_CREDS = Path.home() / ".config/simmer/credentials.json"

# ── helpers ───────────────────────────────────────────────────────────────────

def hl_post(payload):
    return requests.post(HL_API, json=payload, timeout=10).json()

def load_config():
    return json.loads(CONFIG_PATH.read_text())

def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))

# ── 1. portfolio snapshot ─────────────────────────────────────────────────────

def get_portfolio():
    mids  = hl_post({"type": "allMids"})
    perp  = hl_post({"type": "clearinghouseState", "user": HL_ADDRESS})
    spot  = hl_post({"type": "spotClearinghouseState", "user": HL_ADDRESS})

    perp_val  = float(perp.get("marginSummary", {}).get("accountValue", 0))
    positions = [p for p in perp.get("assetPositions", []) if float(p["position"]["szi"]) != 0]

    balances  = {b["coin"]: float(b["total"]) for b in spot.get("balances", []) if float(b.get("total", 0)) > 0}
    hype_val  = balances.get("HYPE", 0) * float(mids.get("HYPE", 0))
    ubtc_val  = balances.get("UBTC", 0) * float(mids.get("UBTC", mids.get("BTC", 0)))
    usdc_spot = balances.get("USDC", 0)
    hype_px   = float(mids.get("HYPE", 0))
    ubtc_px   = float(mids.get("UBTC", mids.get("BTC", 0)))

    return {
        "perp_val":    perp_val,
        "hype_val":    hype_val,
        "ubtc_val":    ubtc_val,
        "usdc_spot":   usdc_spot,
        "hype_px":     hype_px,
        "ubtc_px":     ubtc_px,
        "hype_qty":    balances.get("HYPE", 0),
        "ubtc_qty":    balances.get("UBTC", 0),
        "total_hl":    perp_val + hype_val + ubtc_val + usdc_spot,
        "open_perps":  positions,
        "balances":    balances,
    }

# ── 2. alphastrike scan ───────────────────────────────────────────────────────

def run_alphastrike():
    try:
        result = subprocess.run(
            ["uv", "run", "python", "scripts/signal.py", "--all"],
            cwd=str(ALPHASTRIKE),
            capture_output=True, text=True, timeout=60
        )
        return result.stdout.strip() if result.returncode == 0 else f"AlphaStrike error: {result.stderr[:200]}"
    except Exception as e:
        return f"AlphaStrike unavailable: {e}"

# ── 3. simmer briefing ────────────────────────────────────────────────────────

def get_simmer_briefing():
    try:
        api_key = json.loads(SIMMER_CREDS.read_text())["api_key"]
        r = requests.get(
            "https://api.simmer.markets/api/sdk/briefing",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        if r.status_code == 200:
            b = r.json()
            return {
                "risk_alerts":     b.get("risk_alerts", []),
                "high_divergence": b.get("opportunities", {}).get("high_divergence", [])[:3],
                "new_markets":     b.get("opportunities", {}).get("new_markets", [])[:3],
                "positions":       b.get("positions", {}),
            }
        return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# ── 4. risk check ─────────────────────────────────────────────────────────────

def check_circuit_breakers(cfg, portfolio):
    state    = cfg["state"]
    targets  = cfg["profit_targets"]
    breakers = cfg["circuit_breakers"]
    alerts   = []

    # Daily PnL gates
    if state["today_pnl_usd"] >= targets["daily_target_usd"]:
        alerts.append(f"🎯 DAILY TARGET HIT: ${state['today_pnl_usd']:.2f} >= ${targets['daily_target_usd']}. STOP NEW TRADES.")
        state["trading_paused"] = True

    if state["today_pnl_usd"] <= targets["daily_stop_loss_usd"]:
        alerts.append(f"🛑 DAILY STOP HIT: ${state['today_pnl_usd']:.2f}. FLAT + NO MORE TRADES TODAY.")
        state["trading_paused"] = True

    if state["consecutive_losses"] >= breakers["consecutive_losses"]:
        alerts.append(f"⚠️ {state['consecutive_losses']} CONSECUTIVE LOSSES. Pausing trading.")
        state["trading_paused"] = True

    # Long hold stop-losses
    holds = cfg["long_holds"]
    if portfolio["hype_px"] < holds["hype"]["stop_loss_usd"]:
        alerts.append(f"🔴 HYPE below stop ${holds['hype']['stop_loss_usd']} — currently ${portfolio['hype_px']:.2f}")

    if portfolio["ubtc_px"] < holds["ubtc"]["stop_loss_usd"]:
        alerts.append(f"🔴 BTC below stop ${holds['ubtc']['stop_loss_usd']:,} — currently ${portfolio['ubtc_px']:,.0f}")

    save_config(cfg)
    return alerts

# ── 5. format report ──────────────────────────────────────────────────────────

def format_report(portfolio, alphastrike, simmer, cfg, alerts):
    state   = cfg["state"]
    targets = cfg["profit_targets"]
    lines   = []

    lines.append("📊 **Quant Daily Brief**")
    lines.append(f"🕐 {datetime.now().astimezone().strftime('%a %b %d, %H:%M %Z')}")
    lines.append("")

    # Portfolio
    lines.append("**Portfolio**")
    lines.append(f"  HL Perp:  ${portfolio['perp_val']:.2f}")
    lines.append(f"  UBTC:     {portfolio['ubtc_qty']:.6f} @ ${portfolio['ubtc_px']:,.0f} = ${portfolio['ubtc_val']:.2f}")
    lines.append(f"  HYPE:     {portfolio['hype_qty']:.4f} @ ${portfolio['hype_px']:.2f} = ${portfolio['hype_val']:.2f}")
    lines.append(f"  Simmer:   ~$21.59 USDC")
    lines.append(f"  **Total:  ${portfolio['total_hl'] + 21.59:.2f}**")
    lines.append("")

    # Daily target
    today_pnl = state["today_pnl_usd"]
    pct_done  = (today_pnl / targets["daily_target_usd"] * 100) if targets["daily_target_usd"] > 0 else 0
    lines.append(f"**Daily Target: ${targets['daily_target_usd']} | Today: ${today_pnl:.2f} ({pct_done:.0f}%)**")
    lines.append(f"Stop loss: ${targets['daily_stop_loss_usd']}")
    if state["trading_paused"]:
        lines.append("🚫 TRADING PAUSED")
    lines.append("")

    # Open perp positions
    if portfolio["open_perps"]:
        lines.append("**Open Perp Positions**")
        for p in portfolio["open_perps"]:
            pos = p["position"]
            side = "LONG" if float(pos["szi"]) > 0 else "SHORT"
            lines.append(f"  {pos['coin']} {side}: szi={pos['szi']} uPnL=${float(pos['unrealizedPnl']):.2f}")
        lines.append("")

    # AlphaStrike signals
    lines.append("**AlphaStrike Signals**")
    lines.append(alphastrike[:600] if alphastrike else "  No signals")
    lines.append("")

    # Simmer
    if "error" not in simmer:
        if simmer.get("risk_alerts"):
            lines.append("**⚠️ Simmer Risk Alerts**")
            for a in simmer["risk_alerts"]:
                lines.append(f"  • {a}")
            lines.append("")
        if simmer.get("high_divergence"):
            lines.append("**Simmer Opportunities (high divergence)**")
            for o in simmer["high_divergence"][:3]:
                lines.append(f"  • {o.get('market','?')}: AI={o.get('ai_prob','?')} vs market={o.get('market_prob','?')}")
            lines.append("")

    # Circuit breaker alerts
    if alerts:
        lines.append("**🚨 Alerts**")
        for a in alerts:
            lines.append(f"  {a}")

    return "\n".join(lines)

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    cfg       = load_config()
    portfolio = get_portfolio()
    signals   = run_alphastrike()
    simmer    = get_simmer_briefing()
    alerts    = check_circuit_breakers(cfg, portfolio)

    # Update config with latest prices
    cfg["portfolio"]["hl_perp_usdc"]     = round(portfolio["perp_val"], 2)
    cfg["portfolio"]["hl_spot_ubtc_usd"] = round(portfolio["ubtc_val"], 2)
    cfg["portfolio"]["hl_spot_hype_usd"] = round(portfolio["hype_val"], 2)
    cfg["portfolio"]["total_usd"]        = round(portfolio["total_hl"] + 21.59, 2)
    cfg["state"]["last_updated"]         = datetime.now(timezone.utc).date().isoformat()
    save_config(cfg)

    report = format_report(portfolio, signals, simmer, cfg, alerts)
    print(report)
    return report

if __name__ == "__main__":
    main()
