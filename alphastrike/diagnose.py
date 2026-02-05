#!/usr/bin/env python3
"""
Diagnostic Script - Analyze current losing positions
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../.clawdbot/skills/weex-trading'))

from weex_client import WeexClient


def analyze_positions():
    """Analyze current positions and what went wrong"""
    client = WeexClient()

    print("\n" + "="*80)
    print("ALPHASTRIKE - CURRENT POSITION ANALYSIS")
    print("="*80)

    # Get positions
    positions_result = client.get_positions()

    if not positions_result or not isinstance(positions_result, list):
        print("No positions found or error fetching positions")
        return

    positions = positions_result

    if not positions:
        print("No open positions")
        return

    print(f"\nTotal Open Positions: {len(positions)}")
    print(f"Total Unrealized P&L: ${sum(float(p.get('unrealizePnl', 0)) for p in positions):.2f}")

    for pos in positions:
        symbol = pos.get('symbol', 'UNKNOWN')
        side = pos.get('side', 'UNKNOWN')
        size = float(pos.get('size', 0))
        open_value = float(pos.get('open_value', 0))
        unrealized_pnl = float(pos.get('unrealizePnl', 0))
        leverage = pos.get('leverage', '1')
        margin = float(pos.get('marginSize', 0))

        # Calculate entry price
        entry_price = open_value / size if size > 0 else 0

        # Get current price
        ticker = client.get_ticker(symbol)
        current_price = float(ticker.get('last', entry_price)) if ticker else entry_price

        # Calculate P&L %
        pnl_pct = (unrealized_pnl / margin) * 100 if margin > 0 else 0

        print(f"\n{'─'*80}")
        print(f"SYMBOL: {symbol}")
        print(f"{'─'*80}")
        print(f"Side:       {side}")
        print(f"Leverage:   {leverage}x")
        print(f"Size:       {size}")
        print(f"Entry:      ${entry_price:.4f}")
        print(f"Current:    ${current_price:.4f}")
        print(f"Margin:     ${margin:.2f}")
        print(f"Open Value: ${open_value:.2f}")
        print(f"Unreal P&L: ${unrealized_pnl:+.2f} ({pnl_pct:+.2f}%)")

        # Analysis
        print(f"\n🔍 ANALYSIS:")

        if side == "SHORT":
            if current_price > entry_price:
                print(f"❌ SHORT position underwater - price moved UP")
                print(f"   This suggests entering SHORT in an uptrend (or reversal failed)")
                print(f"   Possible issues:")
                print(f"   • No clear downtrend confirmation (EMA 9 < EMA 20)")
                print(f"   • RSI not overbought (>70)")
                print(f"   • No extreme funding rate to signal squeeze")
                print(f"   • Shorting strong market without reversal signals")
            else:
                print(f"✅ SHORT position profitable")

        print(f"\n💡 RECOMMENDATION:")
        if unrealized_pnl < 0:
            print(f"   These positions were likely opened without proper edge detection.")
            print(f"   Consider closing them to preserve capital for A+ setups.")
            print(f"   AlphaStrike would NOT have opened these positions based on current rules.")

    print(f"\n{'='*80}\n")

    # Get account summary
    assets = client.get_assets()
    if assets and 'data' in assets:
        for asset in assets['data']:
            if asset['coinName'] == 'USDT':
                equity = float(asset['equity'])
                available = float(asset['available'])
                unrealized = float(asset.get('unrealizePnl', 0))

                print(f"ACCOUNT SUMMARY:")
                print(f"  Equity:         ${equity:.2f}")
                print(f"  Available:      ${available:.2f}")
                print(f"  Unrealized P&L: ${unrealized:+.2f}")
                print(f"  Used Margin:    ${equity - available:+.2f}")
                print()


if __name__ == "__main__":
    analyze_positions()
