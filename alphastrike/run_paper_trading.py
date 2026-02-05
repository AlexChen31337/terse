#!/usr/bin/env python3
"""
AlphaStrike v2.0 Paper Trading Runner
Runs in simulation mode continuously, checking for signals every 5 minutes
"""

import sys
import time
from datetime import datetime
from alphastrike import AlphaStrikeBot


def main():
    print("=" * 80)
    print("AlphaStrike v2.0 - Paper Trading Mode")
    print("=" * 80)
    print("Philosophy: Trade Big, Trade Less, Trade with Confidence")
    print("Simulation: ON (no real trades)")
    print("=" * 80)
    print()

    # Initialize bot in simulation mode with $10K starting capital
    bot = AlphaStrikeBot(simulation_mode=True, enable_notifications=True)
    bot.equity = 10000.0  # Set starting equity to $10,000
    
    print(f"Starting equity: ${bot.equity:.2f}")
    print(f"Universe: {', '.join(bot.universe)}")
    print()
    print("Starting trading loop... (Ctrl+C to stop)")
    print()

    iteration = 0
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n[{timestamp}] Iteration #{iteration}")
            print("-" * 60)
            
            # Run one trading cycle
            bot.run_once()
            
            # Show current status
            equity = bot.get_account_equity()
            positions = bot.get_open_positions()
            state = bot.load_state() or {}
            
            print(f"\nStatus:")
            print(f"  Equity: ${equity:.2f}")
            print(f"  Open Positions: {len(positions)}")
            print(f"  Trades Today: {state.get('trades_today', 0)}/2")
            print(f"  Daily P&L: ${state.get('daily_pnl', 0):.2f}")
            
            if positions:
                print(f"\n  Active Positions:")
                for pos in positions:
                    pnl_pct = (pos['unrealized_pnl'] / pos['margin']) * 100 if pos['margin'] > 0 else 0
                    print(f"    • {pos['symbol']}: {pos['side']} {pos['size']} @ {pos['entry_price']:.4f} | "
                          f"P&L: ${pos['unrealized_pnl']:.2f} ({pnl_pct:+.1f}%)")
            
            # Wait 5 minutes before next check
            print(f"\nNext check in 5 minutes...")
            time.sleep(300)  # 5 minutes
            
    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("Paper trading stopped by user")
        print("=" * 80)
        
        # Final summary
        state = bot.load_state() or {}
        final_equity = bot.get_account_equity()
        starting_equity = 10000.0
        total_pnl = final_equity - starting_equity
        
        print(f"\nFinal Summary:")
        print(f"  Starting Equity: ${starting_equity:.2f}")
        print(f"  Final Equity: ${final_equity:.2f}")
        print(f"  Total P&L: ${total_pnl:.2f} ({(total_pnl/starting_equity)*100:+.1f}%)")
        print(f"  Total Trades: {state.get('total_trades', 0)}")
        print(f"  Win Rate: {state.get('win_rate', 0):.1f}%")
        print()


if __name__ == "__main__":
    main()
