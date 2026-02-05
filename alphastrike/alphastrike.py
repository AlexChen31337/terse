#!/usr/bin/env python3
"""
AlphaStrike Trading Bot v2.0
Implements "Trade Big, Trade Less, Trade with Confidence" philosophy

PHILOSOPHY:
- Trade Less: Max 2 trades/day, 4-hour cooldown, max 2 positions
- Trade with Confidence: Only A+ setups (conviction-based filtering)
- Trade Big: Conviction 5 gets 20x leverage, 6% risk, 80% equity allocation

CONVICTION SCALING:
  Conv 1-2: 1.5% risk, 2x leverage, 2.5% stop   → Conservative
  Conv 3:   2.5% risk, 5x leverage, 2.0% stop   → Standard
  Conv 4:   4.0% risk, 10x leverage, 2.0% stop  → Aggressive
  Conv 5:   6.0% risk, 20x leverage, 1.5% stop  → FULL SEND 🚀

POSITION MANAGEMENT:
  Conv 1-4: Partial exits at +3% and +6%
  Conv 5:   LET IT RUN to +12% (no partials)
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add parent directory to path to import weex_client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../.clawdbot/skills/weex-trading'))
from weex_client import WeexClient

from signals import SignalGenerator
from market_data import MarketData
from notifications import NotificationManager


class AlphaStrikeBot:
    """Main trading bot implementing AlphaStrike strategy"""

    def __init__(self, simulation_mode: bool = True, enable_notifications: bool = True):
        self.simulation_mode = simulation_mode
        self.client = WeexClient()
        self.signal_gen = SignalGenerator()
        self.market_data = MarketData()
        self.notifications = NotificationManager() if enable_notifications else None

        # Trading universe - expanded for more opportunities
        self.universe = [
            'cmt_btcusdt',   # Bitcoin - highest liquidity
            'cmt_ethusdt',   # Ethereum - second highest
            'cmt_solusdt',   # Solana - high volatility
            'cmt_dogeusdt',  # Dogecoin - sentiment-driven
            'cmt_xrpusdt',   # XRP - news-sensitive
            'cmt_adausdt',   # Cardano - development-driven
            'cmt_bnbusdt',   # BNB - exchange token
            'cmt_ltcusdt'    # Litecoin - Bitcoin correlation
        ]

        # Risk parameters - PHILOSOPHY: "Trade Big, Trade Less, Trade with Confidence"
        self.equity = 733.0  # Starting equity
        self.max_risk_per_trade = 0.06  # 6% max risk on Conviction 5 (A+ setups)
        self.max_positions = 2          # Trade Less: limit concurrent positions
        self.max_daily_trades = 2       # Trade Less: max 2 trades per day
        self.trade_cooldown_minutes = 240  # Trade Less: 4-hour cooldown between trades

        # State
        self.positions = []
        self.trade_history = []
        self.daily_trade_count = 0
        self.last_trade_time = 0
        self.daily_pnl = 0.0

        # Load state from file if exists
        self.load_state()

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        self.append_to_log(message, level)

    def append_to_log(self, message: str, level: str):
        """Append to log file"""
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f"alphastrike_{datetime.now().strftime('%Y%m%d')}.log")

        with open(log_file, 'a') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}\n")

    def load_state(self):
        """Load bot state from file"""
        state_file = os.path.join(os.path.dirname(__file__), 'state.json')

        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.positions = state.get('positions', [])
                    self.trade_history = state.get('trade_history', [])
                    self.equity = state.get('equity', self.equity)
                    self.daily_trade_count = state.get('daily_trade_count', 0)
                    self.last_trade_time = state.get('last_trade_time', 0)
                    self.daily_pnl = state.get('daily_pnl', 0.0)
                self.log("Loaded state from file")
            except Exception as e:
                self.log(f"Error loading state: {e}", "ERROR")

    def save_state(self):
        """Save bot state to file"""
        state_file = os.path.join(os.path.dirname(__file__), 'state.json')

        try:
            state = {
                'positions': self.positions,
                'trade_history': self.trade_history,
                'equity': self.equity,
                'daily_trade_count': self.daily_trade_count,
                'last_trade_time': self.last_trade_time,
                'daily_pnl': self.daily_pnl,
                'last_updated': int(time.time())
            }

            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.log(f"Error saving state: {e}", "ERROR")

    def get_account_equity(self) -> float:
        """Get current account equity"""
        if self.simulation_mode:
            return self.equity

        try:
            assets = self.client.get_assets()
            if assets and 'data' in assets:
                for asset in assets['data']:
                    if asset['coinName'] == 'USDT':
                        return float(asset['equity'])
        except Exception as e:
            self.log(f"Error getting equity: {e}", "ERROR")

        return self.equity

    def get_open_positions(self) -> List[dict]:
        """Get current open positions"""
        if self.simulation_mode:
            return self.positions

        try:
            result = self.client.get_positions()
            if result and 'data' in result:
                return result['data']
        except Exception as e:
            self.log(f"Error getting positions: {e}", "ERROR")

        return []

    def calculate_position_size(self, signal: dict) -> dict:
        """
        Calculate position size based on conviction level
        PHILOSOPHY: Trade Big, Trade Less, Trade with Confidence
        
        Returns: {margin, size, notional, stop_loss, take_profit}
        """
        conviction = signal['conviction']
        equity = self.get_account_equity()
        price = signal['market_data']['price']

        # PHILOSOPHY: Scale aggressively with conviction
        # Trade BIG on A+ setups (Conviction 5)
        if conviction <= 2:
            risk_pct = 0.015   # 1.5% risk - low confidence
            leverage = 2
            stop_distance = 0.025  # Wider stop
        elif conviction == 3:
            risk_pct = 0.025   # 2.5% risk
            leverage = 5
            stop_distance = 0.02
        elif conviction == 4:
            risk_pct = 0.04    # 4% risk
            leverage = 10
            stop_distance = 0.02
        else:  # conviction >= 5 - A+ SETUP: FULL SEND 🚀
            risk_pct = 0.06    # 6% risk - TRADE BIG
            leverage = 20      # MAX LEVERAGE on best setups
            stop_distance = 0.015  # Tighter stop for high conviction

        # Calculate position
        risk_capital = equity * risk_pct

        # Position size calculation
        # We want to lose risk_capital if stop is hit
        # Position Size = Risk Capital / (Price * Stop Distance * Leverage)
        notional_value = risk_capital / stop_distance
        margin_required = notional_value / leverage

        # Calculate actual position size in contract units
        # For crypto futures, this depends on contract specs
        # Simplified: we trade in notional value
        size = notional_value / price

        # Calculate stop loss and take profit
        # PHILOSOPHY: Let winners run on Conviction 5 (no partial exits)
        if signal['side'] == 'LONG':
            stop_loss = price * (1 - stop_distance)
            
            if conviction >= 5:
                # A+ setup: Let it run, no partial taking
                take_profit_1 = None
                take_profit_2 = price * 1.12  # +12% full exit
            else:
                # Lower conviction: Take partials
                take_profit_1 = price * 1.03  # +3%
                take_profit_2 = price * 1.06  # +6%
        else:  # SHORT
            stop_loss = price * (1 + stop_distance)
            
            if conviction >= 5:
                # A+ setup: Let it run, no partial taking
                take_profit_1 = None
                take_profit_2 = price * 0.88  # -12% full exit
            else:
                # Lower conviction: Take partials
                take_profit_1 = price * 0.97  # -3%
                take_profit_2 = price * 0.94  # -6%

        return {
            'conviction': conviction,
            'risk_pct': risk_pct * 100,
            'leverage': leverage,
            'size': size,
            'margin': margin_required,
            'notional': notional_value,
            'entry': price,
            'stop_loss': stop_loss,
            'stop_distance_pct': stop_distance * 100,
            'take_profit_1': take_profit_1,
            'take_profit_2': take_profit_2
        }

    def can_trade(self, signal: dict) -> Tuple[bool, str]:
        """Check if we can take this trade"""
        # Check max daily trades
        if self.daily_trade_count >= self.max_daily_trades:
            return (False, f"Max daily trades reached ({self.max_daily_trades})")

        # Check cooldown
        time_since_last = time.time() - self.last_trade_time
        if time_since_last < self.trade_cooldown_minutes * 60:
            remaining = int((self.trade_cooldown_minutes * 60 - time_since_last) / 60)
            return (False, f"Cooldown active ({remaining} minutes remaining)")

        # Check max positions
        open_positions = self.get_open_positions()
        if len(open_positions) >= self.max_positions:
            return (False, f"Max positions reached ({self.max_positions})")

        # Check if already in this symbol
        for pos in open_positions:
            if pos.get('symbol') == signal['symbol']:
                return (False, f"Already have position in {signal['symbol']}")

        # Check position size doesn't exceed equity
        # PHILOSOPHY: Allow bigger positions on high conviction (A+ setups)
        equity = self.get_account_equity()
        pos_calc = self.calculate_position_size(signal)

        # Conviction-based position limit
        if signal['conviction'] >= 5:
            max_margin_pct = 0.80  # 80% on A+ setups - TRADE BIG
        elif signal['conviction'] >= 4:
            max_margin_pct = 0.60  # 60% on good setups
        else:
            max_margin_pct = 0.40  # 40% on lower conviction

        if pos_calc['margin'] > equity * max_margin_pct:
            return (False, f"Position too large ({pos_calc['margin']:.2f} > {equity * max_margin_pct:.2f})")

        return (True, "OK")

    def execute_trade(self, signal: dict) -> bool:
        """Execute a trade based on signal"""
        can_trade, reason = self.can_trade(signal)

        if not can_trade:
            self.log(f"Cannot trade {signal['symbol']}: {reason}")
            return False

        pos_calc = self.calculate_position_size(signal)

        self.log(f"\n{'='*60}")
        self.log(f"EXECUTING TRADE: {signal['symbol']} {signal['side']}")
        self.log(f"{'='*60}")
        self.log(f"Conviction: {pos_calc['conviction']}/5")
        self.log(f"Risk: {pos_calc['risk_pct']:.1f}% of equity")
        self.log(f"Leverage: {pos_calc['leverage']}x")
        self.log(f"Entry: ${pos_calc['entry']:.2f}")
        self.log(f"Size: {pos_calc['size']:.4f} contracts")
        self.log(f"Margin: ${pos_calc['margin']:.2f}")
        self.log(f"Notional: ${pos_calc['notional']:.2f}")
        self.log(f"Stop Loss: ${pos_calc['stop_loss']:.2f} (-{pos_calc['stop_distance_pct']:.1f}%)")
        
        if pos_calc['take_profit_1'] is not None:
            self.log(f"TP1: ${pos_calc['take_profit_1']:.2f} (+3%) [Partial Exit]")
            self.log(f"TP2: ${pos_calc['take_profit_2']:.2f} (+6%) [Full Exit]")
        else:
            self.log(f"TP: ${pos_calc['take_profit_2']:.2f} (+12%) [LET IT RUN 🚀]")
        self.log(f"\nRationale:")
        for reason in signal['reasons']:
            self.log(f"  - {reason}")
        self.log(f"{'='*60}\n")

        # Submit AI log to WEEX
        self.submit_ai_log(signal, pos_calc)

        if self.simulation_mode:
            # Simulate the trade
            position = {
                'id': int(time.time()),
                'symbol': signal['symbol'],
                'side': signal['side'],
                'size': pos_calc['size'],
                'entry_price': pos_calc['entry'],
                'stop_loss': pos_calc['stop_loss'],
                'take_profit_1': pos_calc['take_profit_1'],
                'take_profit_2': pos_calc['take_profit_2'],
                'margin': pos_calc['margin'],
                'leverage': pos_calc['leverage'],
                'conviction': pos_calc['conviction'],
                'entry_time': int(time.time()),
                'status': 'OPEN'
            }

            self.positions.append(position)
            self.daily_trade_count += 1
            self.last_trade_time = int(time.time())

            # Send notification
            if self.notifications:
                self.notifications.notify_trade_entry(position, signal, pos_calc)

            # Log to trade history
            trade_record = {
                'timestamp': int(time.time()),
                'symbol': signal['symbol'],
                'side': signal['side'],
                'entry_price': pos_calc['entry'],
                'size': pos_calc['size'],
                'conviction': pos_calc['conviction'],
                'reasons': signal['reasons'],
                'status': 'FILLED'
            }
            self.trade_history.append(trade_record)

            self.save_state()
            self.log(f"Trade executed (SIMULATION)")
            return True

        else:
            # Real trading
            try:
                # Set leverage
                self.client.set_leverage(signal['symbol'], pos_calc['leverage'])

                # Place order
                if signal['side'] == 'LONG':
                    result = self.client.buy(signal['symbol'], str(pos_calc['size']))
                else:
                    result = self.client.sell(signal['symbol'], str(pos_calc['size']))

                if result and result.get('code') == '0':
                    self.log(f"Trade executed successfully")
                    self.daily_trade_count += 1
                    self.last_trade_time = int(time.time())
                    self.save_state()
                    return True
                else:
                    self.log(f"Trade failed: {result}", "ERROR")
                    return False

            except Exception as e:
                self.log(f"Error executing trade: {e}", "ERROR")
                return False

    def submit_ai_log(self, signal: dict, pos_calc: dict):
        """Submit AI trading log to WEEX API"""
        try:
            # Get current market data for indicators
            ticker = self.market_data.get_ticker(signal['symbol'])
            
            log_data = {
                "symbol": signal['symbol'],
                "stage": "Decision Making",
                "action": f"Open {signal['side']}",
                "reason": "; ".join(signal['reasons']),
                "explanation": f"AlphaStrike detected {signal['side']} signal on {signal['symbol']} with conviction {pos_calc['conviction']}/5. "
                               f"Reasons: {'; '.join(signal['reasons'])}",
                "size": str(pos_calc['size']),
                "price": str(pos_calc['entry']),
                "confidence": str(pos_calc['conviction']),
                "strategy": "AlphaStrike v1.0",
                "current_price": str(ticker.get('last', 'N/A')),
                "indicators": {
                    "rsi": str(signal.get('indicators', {}).get('rsi', 'N/A')),
                    "ema_short": str(signal.get('indicators', {}).get('ema_short', 'N/A')),
                    "ema_long": str(signal.get('indicators', {}).get('ema_long', 'N/A')),
                    "volume_ratio": str(signal.get('indicators', {}).get('volume_ratio', 'N/A')),
                    "funding_rate": str(signal.get('indicators', {}).get('funding_rate', 'N/A'))
                },
                "timestamp": int(time.time() * 1000)
            }

            result = self.client.upload_ai_log(log_data)
            
            if result.get('code') == '00000':
                self.log(f"✓ AI log submitted to WEEX for {signal['symbol']}")
            elif result.get('code') == '40020':
                # Parameter format error - likely API key doesn't have AI log access
                self.log(f"⚠ AI log not supported by this API key (contact WEEX to enable)", "WARNING")
            else:
                self.log(f"⚠ AI log submission failed: {result.get('msg', 'Unknown error')}", "WARNING")
                
        except Exception as e:
            self.log(f"⚠ Could not submit AI log: {e}", "WARNING")

    def manage_positions(self):
        """Manage open positions - update stops, check exits"""
        if self.simulation_mode:
            # In simulation, check if TP/SL hit
            for pos in self.positions[:]:
                current_price = self.market_data.get_ticker(pos['symbol']).get('last', pos['entry_price'])
                current_price = float(current_price)

                if pos['side'] == 'LONG':
                    # Check stop loss
                    if current_price <= pos['stop_loss']:
                        self.close_position(pos, current_price, "Stop Loss")

                    # Check take profit 1 (only if not None - Conviction 5 has None)
                    elif pos['take_profit_1'] is not None and current_price >= pos['take_profit_1'] and pos.get('tp1_hit') != True:
                        # Close 50% at TP1
                        self.close_position(pos, current_price, "TP1 (50%)", partial=0.5)
                        pos['tp1_hit'] = True

                    # Check take profit 2
                    elif current_price >= pos['take_profit_2']:
                        exit_reason = "TP2 🚀" if pos['take_profit_1'] is None else "TP2"
                        self.close_position(pos, current_price, exit_reason)

                else:  # SHORT
                    # Check stop loss
                    if current_price >= pos['stop_loss']:
                        self.close_position(pos, current_price, "Stop Loss")

                    # Check take profit 1 (only if not None - Conviction 5 has None)
                    elif pos['take_profit_1'] is not None and current_price <= pos['take_profit_1'] and pos.get('tp1_hit') != True:
                        self.close_position(pos, current_price, "TP1 (50%)", partial=0.5)
                        pos['tp1_hit'] = True

                    # Check take profit 2
                    elif current_price <= pos['take_profit_2']:
                        exit_reason = "TP2 🚀" if pos['take_profit_1'] is None else "TP2"
                        self.close_position(pos, current_price, exit_reason)

    def close_position(self, position: dict, price: float, reason: str, partial: float = 1.0):
        """Close a position"""
        pnl = 0.0

        if position['side'] == 'LONG':
            pnl = (price - position['entry_price']) * position['size'] * partial
        else:  # SHORT
            pnl = (position['entry_price'] - price) * position['size'] * partial

        pnl_pct = (pnl / position['margin']) * 100

        # Submit AI log for position close
        self.submit_close_log(position, price, reason, partial, pnl)

        self.log(f"\n{'='*60}")
        self.log(f"CLOSING POSITION: {position['symbol']} {position['side']}")
        self.log(f"{'='*60}")
        self.log(f"Entry: ${position['entry_price']:.2f}")
        self.log(f"Exit: ${price:.2f}")
        self.log(f"Reason: {reason}")
        self.log(f"P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        self.log(f"{'='*60}\n")

        # Update equity
        self.equity += pnl
        self.daily_pnl += pnl

        # Send notification (only for full closes)
        if partial >= 1.0 and self.notifications:
            self.notifications.notify_trade_exit(position, price, reason, pnl)

        if partial < 1.0:
            # Partial close
            position['size'] *= (1 - partial)
        else:
            # Full close
            if position in self.positions:
                self.positions.remove(position)

        # Record in trade history
        trade_record = {
            'timestamp': int(time.time()),
            'symbol': position['symbol'],
            'side': position['side'],
            'exit_price': price,
            'exit_reason': reason,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'status': 'CLOSED'
        }
        self.trade_history.append(trade_record)

        self.save_state()

    def submit_close_log(self, position: dict, price: float, reason: str, partial: float, pnl: float):
        """Submit AI log for position closure"""
        try:
            log_data = {
                "symbol": position['symbol'],
                "stage": "Decision Making",
                "action": f"Close {position['side']}",
                "reason": reason,
                "explanation": f"AlphaStrike closing {position['side']} position on {position['symbol']}. "
                               f"Reason: {reason}. P&L: {pnl:+.2f} ({(pnl/position['margin']*100):+.2f}%)",
                "size": str(position['size'] * partial),
                "price": str(price),
                "confidence": str(position.get('conviction', 'N/A')),
                "strategy": "AlphaStrike v1.0",
                "current_price": str(price),
                "indicators": {
                    "entry_price": str(position['entry_price']),
                    "exit_price": str(price),
                    "pnl": f"{pnl:+.2f}",
                    "pnl_pct": f"{(pnl/position['margin']*100):+.2f}%",
                    "partial": str(partial),
                    "hold_time_hours": f"{(time.time() - position['entry_time'])/3600:.1f}"
                },
                "timestamp": int(time.time() * 1000)
            }

            result = self.client.upload_ai_log(log_data)
            
            if result.get('code') == '00000':
                self.log(f"✓ Close log submitted to WEEX for {position['symbol']}")
            elif result.get('code') == '40020':
                # Parameter format error - likely API key doesn't have AI log access
                self.log(f"⚠ AI log not supported by this API key (contact WEEX to enable)", "WARNING")
            else:
                self.log(f"⚠ Close log submission failed: {result.get('msg', 'Unknown error')}", "WARNING")
                
        except Exception as e:
            self.log(f"⚠ Could not submit close log: {e}", "WARNING")

    def scan_and_trade(self):
        """Main loop - scan for signals and execute trades"""
        self.log("Scanning market for A+ setups...")

        signals = self.signal_gen.scan_market(self.universe)

        if signals:
            self.log(f"Found {len(signals)} signal(s)")

            for signal in signals[:self.max_daily_trades]:
                self.execute_trade(signal)
        else:
            self.log("No A+ setups found. Patience.")

    def run_once(self):
        """Run one iteration of the bot"""
        self.log("\n" + "="*60)
        self.log(f"AlphaStrike Bot Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("="*60)

        # Update equity
        self.equity = self.get_account_equity()
        self.log(f"Account Equity: ${self.equity:.2f}")
        self.log(f"Daily P&L: ${self.daily_pnl:+.2f}")
        self.log(f"Open Positions: {len(self.positions)}")
        self.log(f"Daily Trades: {self.daily_trade_count}/{self.max_daily_trades}")

        # Check if we should send daily summary (every 24 hours or at midnight)
        now = datetime.now()
        if self.notifications and now.hour == 23 and now.minute >= 0:
            self.notifications.notify_daily_summary(self.equity, self.daily_pnl)

        # Manage existing positions
        self.manage_positions()

        # Scan for new trades
        if self.daily_trade_count < self.max_daily_trades:
            self.scan_and_trade()

    def run(self, interval_minutes: int = 5):
        """Run bot continuously"""
        self.log(f"Starting AlphaStrike Bot (Simulation: {self.simulation_mode})")
        self.log(f"Scan interval: {interval_minutes} minutes")

        while True:
            try:
                self.run_once()

                # Sleep until next scan
                self.log(f"Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)

            except KeyboardInterrupt:
                self.log("\nBot stopped by user")
                break
            except Exception as e:
                self.log(f"Error in main loop: {e}", "ERROR")
                time.sleep(60)  # Wait 1 minute before retry


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='AlphaStrike Trading Bot')
    parser.add_argument('--live', action='store_true', help='Run in live mode (not simulation)')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=5, help='Scan interval in minutes')
    parser.add_argument('--notify', action='store_true', default=True, help='Enable Telegram notifications (default: True)')
    parser.add_argument('--no-notify', action='store_false', dest='notify', help='Disable Telegram notifications')

    args = parser.parse_args()

    # Load Telegram Chat ID from .env if exists
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if line.startswith('TELEGRAM_CHAT_ID='):
                    os.environ['TELEGRAM_CHAT_ID'] = line.strip().split('=', 1)[1]

    bot = AlphaStrikeBot(simulation_mode=not args.live, enable_notifications=args.notify)

    if args.once:
        bot.run_once()
    else:
        bot.run(interval_minutes=args.interval)


if __name__ == "__main__":
    main()
