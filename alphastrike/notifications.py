#!/usr/bin/env python3
"""
Notification system for AlphaStrike trading bot
Sends Telegram alerts and daily summaries
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List


class NotificationManager:
    """Handle trade notifications via Telegram"""

    def __init__(self, telegram_chat_id: str = None):
        self.telegram_chat_id = telegram_chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        self.daily_trades = []
        self.daily_start = datetime.now().date()

    def send_telegram(self, message: str):
        """Send message via Telegram using clawdbot message command"""
        if not self.telegram_chat_id:
            print("[NOTIFY] Telegram Chat ID not set, skipping notification")
            return

        try:
            # Use clawdbot message command
            result = subprocess.run(
                ['clawdbot', 'message', 'send',
                 '--channel', 'telegram',
                 '--target', self.telegram_chat_id,
                 '--message', message],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"[NOTIFY] ✓ Telegram sent: {message[:50]}...")
            else:
                print(f"[NOTIFY] ✗ Telegram failed: {result.stderr}")

        except Exception as e:
            print(f"[NOTIFY] ✗ Error sending Telegram: {e}")

    def notify_trade_entry(self, trade: Dict, signal: Dict, pos_calc: Dict):
        """Send notification when trade is opened"""
        emoji = "🟢" if trade['side'] == 'LONG' else "🔴"

        message = f"""
{emoji} AlphaStrike: {trade['side']} Position Opened

Symbol: {trade['symbol']}
Size: {pos_calc['size']:.4f} contracts
Entry: ${pos_calc['entry']:.2f}
Leverage: {pos_calc['leverage']}x
Risk: {pos_calc['risk_pct']:.1f}% of equity
Conviction: {pos_calc['conviction']}/5

🎯 Targets:
  TP1: ${pos_calc['take_profit_1']:.2f} (+3%)
  TP2: ${pos_calc['take_profit_2']:.2f} (+6%)
  SL: ${pos_calc['stop_loss']:.2f} (-{abs((pos_calc['stop_loss']/pos_calc['entry']-1)*100):.2f}%)

📊 Analysis:
{chr(10).join(f"  • {r}" for r in signal['reasons'])}

📈 Indicators:
  RSI: {signal.get('indicators', {}).get('rsi', 'N/A')}
  EMA Short: {signal.get('indicators', {}).get('ema_short', 'N/A')}
  EMA Long: {signal.get('indicators', {}).get('ema_long', 'N/A')}
  Volume Ratio: {signal.get('indicators', {}).get('volume_ratio', 'N/A')}x
  Funding Rate: {signal.get('indicators', {}).get('funding_rate', 'N/A')}%

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_telegram(message.strip())

        # Track for daily summary
        self.daily_trades.append({
            'type': 'ENTRY',
            'time': datetime.now(),
            'symbol': trade['symbol'],
            'side': trade['side'],
            'entry': pos_calc['entry'],
            'size': pos_calc['size'],
            'conviction': pos_calc['conviction']
        })

    def notify_trade_exit(self, position: Dict, exit_price: float, reason: str, pnl: float):
        """Send notification when trade is closed"""
        emoji = "✅" if pnl > 0 else "❌"
        pnl_pct = (pnl / position['margin'] * 100)

        message = f"""
{emoji} AlphaStrike: {position['side']} Position Closed

Symbol: {position['symbol']}
Entry: ${position['entry_price']:.2f}
Exit: ${exit_price:.2f}
Size: {position['size']:.4f} contracts
Reason: {reason.upper()}

💰 P&L: {pnl:+.2f} USDT ({pnl_pct:+.2f}%)
Hold Time: {(datetime.now().timestamp() - position['entry_time'])/3600:.1f}h

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_telegram(message.strip())

        # Track for daily summary
        self.daily_trades.append({
            'type': 'EXIT',
            'time': datetime.now(),
            'symbol': position['symbol'],
            'side': position['side'],
            'entry': position['entry_price'],
            'exit': exit_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'reason': reason
        })

    def notify_daily_summary(self, equity: float, daily_pnl: float):
        """Send end-of-day summary report"""
        today = datetime.now().date()

        # Reset if new day
        if today != self.daily_start:
            self.daily_trades = []
            self.daily_start = today
            return

        if not self.daily_trades:
            return

        # Calculate stats
        entries = [t for t in self.daily_trades if t['type'] == 'ENTRY']
        exits = [t for t in self.daily_trades if t['type'] == 'EXIT']
        total_pnl = sum(t.get('pnl', 0) for t in exits)
        wins = [t for t in exits if t.get('pnl', 0) > 0]
        losses = [t for t in exits if t.get('pnl', 0) <= 0]

        win_rate = (len(wins) / len(exits) * 100) if exits else 0

        message = f"""
📊 AlphaStrike Daily Report
{datetime.now().strftime('%Y-%m-%d')}

💰 Account:
  Equity: ${equity:.2f}
  Daily P&L: {daily_pnl:+.2f} USDT
  Total P&L: {total_pnl:+.2f} USDT

📈 Performance:
  Trades Opened: {len(entries)}
  Trades Closed: {len(exits)}
  Wins: {len(wins)}
  Losses: {len(losses)}
  Win Rate: {win_rate:.1f}%

📝 Trade Log:
"""

        for trade in self.daily_trades:
            if trade['type'] == 'ENTRY':
                message += f"\n  🟢 {trade['time'].strftime('%H:%M')} | {trade['symbol']} {trade['side']} @ ${trade['entry']:.2f} | Conviction: {trade['conviction']}/5"
            else:
                emoji = "✅" if trade['pnl'] > 0 else "❌"
                message += f"\n  {emoji} {trade['time'].strftime('%H:%M')} | {trade['symbol']} {trade['side']} closed @ ${trade['exit']:.2f} | {trade['pnl']:+.2f} ({trade['pnl_pct']:+.2f}%) | {trade['reason']}"

        message += f"\n\n⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        self.send_telegram(message.strip())

    def reset_daily(self):
        """Reset daily trade tracking"""
        self.daily_trades = []
        self.daily_start = datetime.now().date()
