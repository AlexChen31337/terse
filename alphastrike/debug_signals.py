#!/usr/bin/env python3
"""
Debug signal rejection - show why signals are being rejected
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../.clawdbot/skills/weex-trading'))

from signals import SignalGenerator
from market_data import MarketData

def main():
    sg = SignalGenerator()
    md = MarketData()

    symbols = ['cmt_btcusdt', 'cmt_ethusdt', 'cmt_solusdt', 'cmt_bnbusdt', 'cmt_dogeusdt']

    print('='*80)
    print('SIGNAL REJECTION ANALYSIS')
    print('='*80)
    print()

    for symbol in symbols:
        print(f'📊 {symbol.replace("cmt_", "").upper()}')
        
        # Get market data
        data = md.get_market_data(symbol)
        
        if not data:
            print(f'   ❌ Could not fetch market data')
            print()
            continue
        
        price = data.get('price', 0)
        change_24h = data.get('price_change_24h', 0)
        rsi = data.get('rsi', 50)
        ema_9 = data.get('ema_9', 0)
        ema_20 = data.get('ema_20', 0)
        ema_50 = data.get('ema_50', 0)
        funding = data.get('funding_rate', 0)
        
        print(f'   Price: ${price:,.2f} ({change_24h:+.2f}% 24h)')
        print(f'   RSI: {rsi:.1f}')
        print(f'   EMA 9: ${ema_9:,.2f}')
        print(f'   EMA 20: ${ema_20:,.2f}')
        print(f'   EMA 50: ${ema_50:,.2f}')
        print(f'   Funding: {funding:.6f}')
        print()
        
        # Check LONG
        is_long, conv_long, reasons_long = sg.evaluate_long_setup(data)
        if is_long:
            print(f'   ✅ LONG SIGNAL (Conviction {conv_long}/5):')
            for r in reasons_long:
                print(f'      • {r}')
        else:
            print(f'   ❌ LONG REJECTED:')
            for r in reasons_long:
                print(f'      • {r}')
        
        print()
        
        # Check SHORT
        is_short, conv_short, reasons_short = sg.evaluate_short_setup(data)
        if is_short:
            print(f'   ✅ SHORT SIGNAL (Conviction {conv_short}/5):')
            for r in reasons_short:
                print(f'      • {r}')
        else:
            print(f'   ❌ SHORT REJECTED:')
            for r in reasons_short:
                print(f'      • {r}')
        
        print()
        print('-'*80)
        print()

    print('='*80)
    print()
    print('💡 KEY INSIGHTS:')
    print('   • Signals need conviction ≥3 to trigger')
    print('   • Conviction 5 = A+ setup (20x leverage in v2.0)')
    print('   • If all rejected, market conditions not ideal for entry')
    print()

if __name__ == "__main__":
    main()
