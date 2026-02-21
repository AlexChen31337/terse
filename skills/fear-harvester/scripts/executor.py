#!/usr/bin/env python3
"""
FearHarvester Executor — DCA engine targeting Hyperliquid spot (UBTC/USDC).

Modes:
  --dry-run   Simulate only, no state written
  --paper     Track positions locally (no exchange calls)
  --live      Execute real trades on HL spot via API

Strategy: DCA when F&G <= 20, hold 120 days
Exchange: Hyperliquid spot, UBTC/USDC (@142)

Usage:
    uv run python scripts/executor.py --dry-run          # simulate only
    uv run python scripts/executor.py --paper             # paper trading
    uv run python scripts/executor.py --live              # real money on HL
    uv run python scripts/executor.py --status            # show positions + P&L
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
UBTC_PAIR = "@142"  # Hyperliquid spot pair index for UBTC/USDC
UBTC_SZ_DECIMALS = 5  # Hyperliquid szDecimals for UBTC
UBTC_PX_DECIMALS = 1  # Price precision (1 decimal place)
DEFAULT_HOLD_DAYS = 120
DEFAULT_BUY_THRESHOLD = 20  # F&G ≤ 20 → buy
DEFAULT_SELL_THRESHOLD = 50  # F&G ≥ 50 → consider rebalance
STATE_FILE = Path(__file__).parent.parent / "data" / "executor_state.json"

logger = logging.getLogger("fear-harvester.executor")

# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def load_state() -> dict[str, Any]:
    """Load executor state from disk."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {
        "positions": [],
        "total_invested": 0.0,
        "mode": "paper",
        "last_action": None,
        "version": 2,
    }


def save_state(state: dict[str, Any]) -> None:
    """Persist executor state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# Market data
# ---------------------------------------------------------------------------

def get_fear_greed() -> dict[str, Any]:
    """Fetch current Fear & Greed index from alternative.me."""
    resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10)
    resp.raise_for_status()
    d = resp.json()["data"][0]
    return {"value": int(d["value"]), "label": d["value_classification"]}


def get_btc_price() -> float:
    """Fetch BTC/USDT price from Binance as fallback reference."""
    resp = requests.get(
        "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10
    )
    resp.raise_for_status()
    return float(resp.json()["price"])


# ---------------------------------------------------------------------------
# Hyperliquid credentials
# ---------------------------------------------------------------------------

HL_ENV_PATH = Path("/home/bowen/.openclaw/skills/hyperliquid/.env")


def load_hl_credentials() -> tuple[Optional[str], Optional[str]]:
    """
    Load HL private key and wallet address from environment.

    Checks:
      1. .env file at HL skill location
      2. Environment variables HL_PRIVATE_KEY / PRIVATE_KEY
      3. Environment variables HL_WALLET_ADDRESS / WALLET_ADDRESS
    """
    if HL_ENV_PATH.exists():
        for line in HL_ENV_PATH.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    private_key = os.environ.get("HL_PRIVATE_KEY") or os.environ.get("PRIVATE_KEY")
    wallet_address = os.environ.get("HL_WALLET_ADDRESS") or os.environ.get("WALLET_ADDRESS")
    return private_key, wallet_address


# ---------------------------------------------------------------------------
# HLSpotExecutor — wraps HL client for UBTC spot orders
# ---------------------------------------------------------------------------

class HLSpotExecutor:
    """Execute spot orders on Hyperliquid for UBTC/USDC."""

    def __init__(
        self,
        private_key: Optional[str] = None,
        wallet_address: Optional[str] = None,
        testnet: bool = False,
    ):
        self.private_key = private_key
        self.wallet_address = wallet_address
        self.testnet = testnet
        self._client: Any = None  # Lazy-loaded HyperliquidClient

    @property
    def client(self) -> Any:
        """Lazy-load the HL client (avoids import overhead in dry-run)."""
        if self._client is None:
            # Add HL scripts to path so we can import the client
            hl_scripts = Path("/home/bowen/.openclaw/skills/hyperliquid/scripts")
            if str(hl_scripts) not in sys.path:
                sys.path.insert(0, str(hl_scripts))
            from client import HyperliquidClient  # type: ignore[import-not-found]

            if not self.private_key:
                raise ValueError(
                    "HL_PRIVATE_KEY required for live trading. "
                    "Set via environment or .env file."
                )
            self._client = HyperliquidClient(
                private_key=self.private_key, testnet=self.testnet
            )
        return self._client

    def get_ubtc_mid_price(self) -> float:
        """Get current UBTC mid price from HL."""
        mids = self.client.get_all_mids()
        price_str = mids.get(UBTC_PAIR)
        if price_str is None:
            raise ValueError(f"UBTC pair {UBTC_PAIR} not found in HL mids")
        return float(price_str)

    def get_ubtc_best_ask(self) -> float:
        """Get best ask price from UBTC order book."""
        book = self.client.get_l2_book(UBTC_PAIR)
        asks = book.get("levels", [[], []])[1]
        if not asks:
            raise ValueError("No asks in UBTC order book")
        return float(asks[0]["px"])

    def get_spot_meta(self) -> dict[str, Any]:
        """Get spot market metadata."""
        return self.client.get_spot_meta()

    def _get_spot_asset_index(self) -> int:
        """
        Get the asset index for UBTC spot pair.

        On HL, spot asset indices in order actions use 10000 + token_index.
        The token_index for UBTC/USDC is 142.
        """
        return 10000 + 142

    def place_spot_market_buy(self, amount_usdc: float, price: Optional[float] = None) -> dict[str, Any]:
        """
        Buy UBTC with USDC at market price.

        Places an IOC (Immediate-or-Cancel) limit order at 1% above mid
        to simulate a market buy on HL spot.

        Args:
            amount_usdc: USD amount to spend
            price: Optional override price (uses mid price if None)

        Returns:
            HL API order response
        """
        if price is None:
            price = self.get_ubtc_mid_price()

        # Size in base asset (BTC), rounded to szDecimals
        btc_size = round(amount_usdc / price, UBTC_SZ_DECIMALS)
        if btc_size <= 0:
            raise ValueError(f"Order size too small: {btc_size} BTC from ${amount_usdc}")

        # IOC limit at 1% above mid acts as aggressive market buy
        limit_price = round(price * 1.01, UBTC_PX_DECIMALS)

        asset_index = self._get_spot_asset_index()

        # Build the order action directly (spot uses 10000+index)
        order = {
            "a": asset_index,
            "b": True,
            "p": str(limit_price),
            "s": str(btc_size),
            "r": False,
            "t": {"limit": {"tif": "Ioc"}},
        }

        action = {
            "type": "order",
            "orders": [order],
            "grouping": "na",
        }

        result = self.client._exchange_request(action)
        logger.info(
            "Spot buy: %.5f UBTC @ limit $%.1f (mid $%.1f) — result: %s",
            btc_size, limit_price, price, result.get("status", "unknown"),
        )
        return result

    def place_spot_market_sell(self, btc_size: float, price: Optional[float] = None) -> dict[str, Any]:
        """
        Sell UBTC for USDC at market price.

        Places an IOC limit order at 1% below mid to simulate market sell.

        Args:
            btc_size: Amount of BTC to sell
            price: Optional override price

        Returns:
            HL API order response
        """
        if price is None:
            price = self.get_ubtc_mid_price()

        btc_size = round(btc_size, UBTC_SZ_DECIMALS)
        if btc_size <= 0:
            raise ValueError(f"Sell size too small: {btc_size} BTC")

        # IOC limit at 1% below mid acts as aggressive market sell
        limit_price = round(price * 0.99, UBTC_PX_DECIMALS)

        asset_index = self._get_spot_asset_index()

        order = {
            "a": asset_index,
            "b": False,
            "p": str(limit_price),
            "s": str(btc_size),
            "r": False,
            "t": {"limit": {"tif": "Ioc"}},
        }

        action = {
            "type": "order",
            "orders": [order],
            "grouping": "na",
        }

        result = self.client._exchange_request(action)
        logger.info(
            "Spot sell: %.5f UBTC @ limit $%.1f (mid $%.1f) — result: %s",
            btc_size, limit_price, price, result.get("status", "unknown"),
        )
        return result

    def get_spot_balances(self) -> dict[str, Any]:
        """Get user's spot balances from HL."""
        if not self.wallet_address:
            raise ValueError("Wallet address required to query balances")
        return self.client.get_spot_user_state(self.wallet_address)

    def get_user_fills(self, start_time: Optional[int] = None) -> list[dict[str, Any]]:
        """Get user's recent fills."""
        if not self.wallet_address:
            raise ValueError("Wallet address required to query fills")
        if start_time:
            return self.client.get_user_fills_by_time(self.wallet_address, start_time)
        return self.client.get_user_fills(self.wallet_address)

    def close(self) -> None:
        """Clean up client resources."""
        if self._client is not None:
            self._client.close()
            self._client = None


# ---------------------------------------------------------------------------
# Decision engine
# ---------------------------------------------------------------------------

def decide(fg_value: int, state: dict[str, Any], config: dict[str, Any]) -> str:
    """
    Return action: DCA_BUY | REBALANCE_YIELD | HOLD.

    DCA_BUY: F&G ≤ buy_threshold and haven't hit max capital
    REBALANCE_YIELD: F&G ≥ sell_threshold and have open positions older than hold_days
    HOLD: otherwise
    """
    if fg_value <= config["buy_threshold"]:
        invested = state["total_invested"]
        max_invest = config["max_capital"]
        if invested < max_invest:
            return "DCA_BUY"

    if fg_value >= config["sell_threshold"]:
        hold_days = config.get("hold_days", DEFAULT_HOLD_DAYS)
        now = datetime.now()
        for pos in state["positions"]:
            if pos["status"] != "open":
                continue
            entry_time = datetime.fromisoformat(pos["timestamp"])
            if (now - entry_time).days >= hold_days:
                return "REBALANCE_YIELD"

    return "HOLD"


# ---------------------------------------------------------------------------
# Execution functions
# ---------------------------------------------------------------------------

def execute_dca_buy(
    price: float,
    fg: int,
    state: dict[str, Any],
    config: dict[str, Any],
    *,
    mode: str = "dry-run",
    hl_executor: Optional[HLSpotExecutor] = None,
) -> str:
    """
    Execute a DCA buy.

    Modes:
        dry-run: simulate, no state change, no API call
        paper:   update local state, no API call
        live:    place real order on HL + update local state
    """
    dca_amount = config["dca_amount_usd"]
    btc_qty = round(dca_amount / price, UBTC_SZ_DECIMALS)

    hl_order_id: Optional[str] = None
    fill_price = price

    # Live mode: place real order
    if mode == "live":
        if hl_executor is None:
            raise ValueError("HLSpotExecutor required for live mode")
        result = hl_executor.place_spot_market_buy(dca_amount, price=price)
        status = result.get("status")
        if status != "ok":
            err_msg = result.get("response", "Unknown error")
            return f"❌ LIVE ORDER FAILED: {err_msg}"
        # Extract fill info
        statuses = result.get("response", {}).get("data", {}).get("statuses", [])
        if statuses:
            fill_info = statuses[0]
            if "filled" in fill_info:
                hl_order_id = str(fill_info["filled"].get("oid", ""))
                fill_price = float(fill_info["filled"].get("avgPx", price))
                btc_qty = float(fill_info["filled"].get("totalSz", btc_qty))
            elif "resting" in fill_info:
                hl_order_id = str(fill_info["resting"].get("oid", ""))

    pos = {
        "timestamp": datetime.now().isoformat(),
        "entry_price": fill_price,
        "btc_qty": btc_qty,
        "usd_amount": dca_amount,
        "fg_at_entry": fg,
        "status": "open",
        "mode": mode,
        "hl_order_id": hl_order_id,
    }

    # Update state for paper and live modes
    if mode in ("paper", "live"):
        state["positions"].append(pos)
        state["total_invested"] += dca_amount
        state["last_action"] = (
            f"DCA_BUY ${dca_amount:.0f} @ ${fill_price:,.0f} (F&G={fg}) [{mode}]"
        )
        state["mode"] = mode
        save_state(state)

    prefix = {"dry-run": "[DRY RUN] ", "paper": "[PAPER] ", "live": ""}[mode]
    oid_info = f" | oid={hl_order_id}" if hl_order_id else ""
    return (
        f"{prefix}DCA BUY ${dca_amount:.0f} UBTC @ ${fill_price:,.2f} "
        f"| qty={btc_qty:.5f} | F&G={fg}{oid_info}"
    )


def execute_rebalance(
    price: float,
    fg: int,
    state: dict[str, Any],
    config: dict[str, Any],
    *,
    mode: str = "dry-run",
    hl_executor: Optional[HLSpotExecutor] = None,
) -> str:
    """
    Rebalance (sell) positions that have exceeded hold_days.

    Only sells positions older than hold_days.
    """
    hold_days = config.get("hold_days", DEFAULT_HOLD_DAYS)
    now = datetime.now()
    eligible = []
    for p in state["positions"]:
        if p["status"] != "open":
            continue
        entry_time = datetime.fromisoformat(p["timestamp"])
        if (now - entry_time).days >= hold_days:
            eligible.append(p)

    if not eligible:
        return f"{'[DRY RUN] ' if mode == 'dry-run' else ''}No positions past {hold_days}d hold period"

    total_btc = sum(p["btc_qty"] for p in eligible)
    total_cost = sum(p["usd_amount"] for p in eligible)
    total_value = total_btc * price
    pnl_pct = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0

    # Live mode: place real sell order
    if mode == "live":
        if hl_executor is None:
            raise ValueError("HLSpotExecutor required for live mode")
        result = hl_executor.place_spot_market_sell(total_btc, price=price)
        status = result.get("status")
        if status != "ok":
            err_msg = result.get("response", "Unknown error")
            return f"❌ LIVE SELL FAILED: {err_msg}"

    # Update state for paper and live modes
    if mode in ("paper", "live"):
        for p in eligible:
            p["status"] = "closed"
            p["exit_price"] = price
            p["exit_timestamp"] = now.isoformat()
            p["pnl_pct"] = ((price - p["entry_price"]) / p["entry_price"]) * 100
        state["total_invested"] -= total_cost
        state["last_action"] = (
            f"REBALANCE ${total_value:,.0f} ({pnl_pct:+.1f}%) @ F&G={fg} [{mode}]"
        )
        save_state(state)

    prefix = {"dry-run": "[DRY RUN] ", "paper": "[PAPER] ", "live": ""}[mode]
    return (
        f"{prefix}REBALANCE {total_btc:.5f} UBTC → ${total_value:,.0f} "
        f"| cost=${total_cost:,.0f} | PnL={pnl_pct:+.1f}% | F&G={fg}"
    )


# ---------------------------------------------------------------------------
# Position summary
# ---------------------------------------------------------------------------

def get_position_summary(state: dict[str, Any], current_price: float) -> dict[str, Any]:
    """
    Build a summary of all positions.

    Returns dict with open/closed counts, total P&L, etc.
    """
    open_positions = [p for p in state["positions"] if p["status"] == "open"]
    closed_positions = [p for p in state["positions"] if p["status"] == "closed"]

    total_btc = sum(p["btc_qty"] for p in open_positions)
    total_cost = sum(p["usd_amount"] for p in open_positions)
    current_value = total_btc * current_price
    unrealized_pnl = current_value - total_cost
    unrealized_pnl_pct = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0

    avg_entry = total_cost / total_btc if total_btc > 0 else 0

    realized_pnl = 0.0
    for p in closed_positions:
        cost = p["usd_amount"]
        exit_val = p["btc_qty"] * p.get("exit_price", 0)
        realized_pnl += exit_val - cost

    return {
        "open_count": len(open_positions),
        "closed_count": len(closed_positions),
        "total_btc": total_btc,
        "avg_entry_price": avg_entry,
        "total_cost": total_cost,
        "current_value": current_value,
        "unrealized_pnl": unrealized_pnl,
        "unrealized_pnl_pct": unrealized_pnl_pct,
        "realized_pnl": realized_pnl,
        "total_invested": state["total_invested"],
        "last_action": state.get("last_action"),
        "mode": state.get("mode", "unknown"),
    }


def show_status(state: dict[str, Any]) -> None:
    """Print a human-readable status report."""
    try:
        price = get_btc_price()
    except Exception:
        price = 0.0
    try:
        fg = get_fear_greed()
    except Exception:
        fg = {"value": -1, "label": "unavailable"}

    summary = get_position_summary(state, price)

    print(f"\n📊 FearHarvester Status (mode: {summary['mode']})")
    print(f"   F&G: {fg['value']} ({fg['label']})")
    print(f"   BTC: ${price:,.2f}")
    print(f"   Exchange: Hyperliquid spot (UBTC/USDC {UBTC_PAIR})")
    print(f"   Open positions: {summary['open_count']}")
    if summary["open_count"] > 0:
        print(f"   Total UBTC: {summary['total_btc']:.5f}")
        print(f"   Avg entry: ${summary['avg_entry_price']:,.2f}")
        print(f"   Current value: ${summary['current_value']:,.2f}")
        print(f"   Unrealized PnL: ${summary['unrealized_pnl']:+,.2f} ({summary['unrealized_pnl_pct']:+.1f}%)")
    if summary["closed_count"] > 0:
        print(f"   Closed positions: {summary['closed_count']}")
        print(f"   Realized PnL: ${summary['realized_pnl']:+,.2f}")
    print(f"   Total invested: ${summary['total_invested']:,.2f}")
    print(f"   Last action: {summary['last_action'] or 'none'}")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="FearHarvester DCA Executor (HL Spot)")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--dry-run", action="store_true", help="Simulate only, no state changes")
    mode_group.add_argument("--paper", action="store_true", help="Paper trading mode (local state, no API)")
    mode_group.add_argument("--live", action="store_true", help="Live trading on Hyperliquid spot")
    parser.add_argument("--status", action="store_true", help="Show current positions and P&L")
    parser.add_argument("--testnet", action="store_true", help="Use HL testnet")
    parser.add_argument(
        "--buy-threshold", type=int, default=DEFAULT_BUY_THRESHOLD,
        help=f"F&G buy threshold (default: {DEFAULT_BUY_THRESHOLD})",
    )
    parser.add_argument(
        "--sell-threshold", type=int, default=DEFAULT_SELL_THRESHOLD,
        help=f"F&G sell threshold (default: {DEFAULT_SELL_THRESHOLD})",
    )
    parser.add_argument(
        "--hold-days", type=int, default=DEFAULT_HOLD_DAYS,
        help=f"Minimum hold period in days (default: {DEFAULT_HOLD_DAYS})",
    )
    parser.add_argument(
        "--dca-amount", type=float, default=500.0,
        help="USD per DCA buy (default: 500)",
    )
    parser.add_argument(
        "--max-capital", type=float, default=5000.0,
        help="Max total capital (default: 5000)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    config: dict[str, Any] = {
        "buy_threshold": args.buy_threshold,
        "sell_threshold": args.sell_threshold,
        "hold_days": args.hold_days,
        "dca_amount_usd": args.dca_amount,
        "max_capital": args.max_capital,
    }

    state = load_state()

    if args.status:
        show_status(state)
        return

    # Determine mode
    if args.live:
        mode = "live"
    elif args.paper:
        mode = "paper"
    else:
        mode = "dry-run"

    # Initialize HL executor for live mode
    hl_executor: Optional[HLSpotExecutor] = None
    if mode == "live":
        private_key, wallet_address = load_hl_credentials()
        if not private_key:
            print("❌ No HL credentials found. Set HL_PRIVATE_KEY or create .env file.")
            print(f"   Expected at: {HL_ENV_PATH}")
            sys.exit(1)
        hl_executor = HLSpotExecutor(
            private_key=private_key,
            wallet_address=wallet_address,
            testnet=args.testnet,
        )

    try:
        fg = get_fear_greed()
        price = get_btc_price()
    except Exception as e:
        print(f"❌ Failed to fetch market data: {e}")
        sys.exit(1)

    action = decide(fg["value"], state, config)

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] "
        f"F&G={fg['value']} ({fg['label']}) | BTC=${price:,.2f} | "
        f"Action={action} | Mode={mode}"
    )

    if action == "DCA_BUY":
        result = execute_dca_buy(
            price, fg["value"], state, config, mode=mode, hl_executor=hl_executor
        )
        print(f"✅ {result}")
    elif action == "REBALANCE_YIELD":
        result = execute_rebalance(
            price, fg["value"], state, config, mode=mode, hl_executor=hl_executor
        )
        print(f"💰 {result}")
    else:
        print(f"✋ HOLD — F&G={fg['value']} not in action zone (buy≤{config['buy_threshold']}, sell≥{config['sell_threshold']})")

    if hl_executor:
        hl_executor.close()


if __name__ == "__main__":
    main()
