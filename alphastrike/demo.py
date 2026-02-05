#!/usr/bin/env python3
"""
AlphaStrike Demo - Show how the bot works
"""

import os
import sys

# Set environment variables for demo
os.environ['WEEX_API_KEY'] = 'demo_key'
os.environ['WEEX_API_SECRET'] = 'demo_secret'
os.environ['WEEX_PASSPHRASE'] = 'demo_pass'
os.environ['WEEX_BASE_URL'] = 'https://api-contract.weex.com'

from alphastrike import AlphaStrikeBot


def main():
    print("\n" + "="*80)
    print("ALPHASTRIKE TRADING BOT DEMO")
    print("="*80)
    print("\nThis demo shows how AlphaStrike evaluates the market")
    print("and decides whether to trade or wait.\n")

    bot = AlphaStrikeBot(simulation_mode=True)

    print("CONFIGURATION:")
    print(f"  Account Equity: ${bot.equity:.2f}")
    print(f"  Max Risk Per Trade: {bot.max_risk_per_trade * 100}%")
    print(f"  Max Positions: {bot.max_positions}")
    print(f"  Max Daily Trades: {bot.max_daily_trades}")
    print(f"  Trade Cooldown: {bot.trade_cooldown_minutes} minutes")
    print(f"  Trading Universe: {len(bot.universe)} symbols")

    print("\n" + "─"*80)
    print("SCANNING MARKET FOR A+ SETUPS...")
    print("─"*80 + "\n")

    # Scan for signals
    signals = bot.signal_gen.scan_market(bot.universe)

    if signals:
        print(f"Found {len(signals)} signal(s):\n")

        for i, signal in enumerate(signals, 1):
            print(f"Signal {i}: {signal['symbol']} - {signal['side']}")
            print(f"  Conviction: {signal['conviction']}/5")

            # Calculate position
            pos_calc = bot.calculate_position_size(signal)

            print(f"  Entry: ${pos_calc['entry']:.2f}")
            print(f"  Stop Loss: ${pos_calc['stop_loss']:.2f} ({abs((pos_calc['stop_loss']/pos_calc['entry']-1)*100):.2f}%)")
            print(f"  TP1: ${pos_calc['take_profit_1']:.2f} (+3%)")
            print(f"  TP2: ${pos_calc['take_profit_2']:.2f} (+6%)")
            print(f"  Risk: ${bot.equity * pos_calc['risk_pct']/100:.2f} ({pos_calc['risk_pct']:.1f}% of equity)")
            print(f"  Margin: ${pos_calc['margin']:.2f} at {pos_calc['leverage']}x leverage")
            print(f"\n  Rationale:")
            for reason in signal['reasons']:
                print(f"    • {reason}")

            # Check if we can trade
            can_trade, msg = bot.can_trade(signal)
            print(f"\n  Can Trade: {can_trade} ({msg})")

            if i < len(signals):
                print("\n" + "─"*80 + "\n")

        print("\n" + "="*80)
        print("DECISION: Would execute highest conviction signals")
        print("="*80)

    else:
        print("✅ No A+ setups found.\n")
        print("This is NORMAL and EXPECTED behavior for AlphaStrike.")
        print("\nAlphaStrike waits for high-conviction setups with:")
        print("  • Clear trend confirmation (EMA alignment)")
        print("  • Momentum confirmation (RSI extremes)")
        print("  • Volume confirmation")
        print("  • Favorable funding rates")
        print("\nWhen in doubt, stay out. Patience > FOMO.")

    print("\n" + "="*80)
    print("CURRENT MARKET CONDITIONS (Sample)")
    print("="*80 + "\n")

    # Show market data for universe
    for symbol in bot.universe:
        data = bot.market_data.get_market_data(symbol)

        if data:
            print(f"{symbol}:")
            print(f"  Price: ${data['price']:.2f}")
            print(f"  RSI: {data['rsi']:.1f}")
            print(f"  EMA 9: ${data['ema_9']:.2f}")
            print(f"  EMA 20: ${data['ema_20']:.2f}")
            print(f"  EMA 50: ${data['ema_50']:.2f}")
            print(f"  Funding Rate: {data['funding_rate']:.4f}")
            print(f"  24h Change: {data['price_change_24h']:+.2f}%")

            # Quick signal check
            is_long, conv_long, reasons_long = bot.signal_gen.evaluate_long_setup(data)
            is_short, conv_short, reasons_short = bot.signal_gen.evaluate_short_setup(data)

            if is_long:
                print(f"  → LONG signal (Conviction: {conv_long}/5)")
            elif is_short:
                print(f"  → SHORT signal (Conviction: {conv_short}/5)")
            else:
                print(f"  → No signal (conditions not met)")

            print()

    print("="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print("\nTo run the bot in simulation mode:")
    print("  cd /home/peter/clawd/alphastrike")
    print("  python3 alphastrike.py --once")
    print("\nTo read the full strategy:")
    print("  cat STRATEGY.md")
    print("\nTo see current positions:")
    print("  python3 diagnose.py")
    print()


if __name__ == "__main__":
    main()
