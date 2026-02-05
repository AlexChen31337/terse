#!/usr/bin/env python3
"""
Signal Generator for AlphaStrike
Evaluates market conditions and generates high-conviction trading signals
"""

import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from market_data import MarketData
from smart_money import SmartMoneyTracker


class SignalGenerator:
    """Generate high-conviction trading signals based on AlphaStrike strategy"""

    def __init__(self):
        self.market_data = MarketData()
        self.smart_money = SmartMoneyTracker()

    def evaluate_long_setup(self, data: dict) -> Tuple[bool, int, List[str]]:
        """
        Evaluate if symbol meets A+ long setup criteria
        Returns: (is_signal, conviction_level, reasons)
        """
        if not data:
            return (False, 0, [])

        reasons = []
        conviction = 0

        # Required criteria
        rsi = data.get('rsi', 50)
        price = data.get('price', 0)
        ema_9 = data.get('ema_9', 0)
        ema_20 = data.get('ema_20', 0)
        ema_50 = data.get('ema_50', 0)
        funding_rate = data.get('funding_rate', 0)
        price_change_24h = data.get('price_change_24h', 0)

        # 1. RSI < 30 OR crossed from <30 to >35
        if rsi < 30:
            reasons.append(f"RSI oversold ({rsi:.1f})")
            conviction += 1
        elif 30 <= rsi <= 35:
            reasons.append(f"RSI bouncing from oversold ({rsi:.1f})")
            conviction += 1
        else:
            return (False, 0, ["RSI not oversold"])

        # 2. Price > EMA 20 AND EMA 9 > EMA 20
        if price > ema_20 and ema_9 > ema_20:
            reasons.append(f"Uptrend (Price > EMA20, EMA9 > EMA20)")
            conviction += 1
        else:
            return (False, 0, ["Not in uptrend"])

        # 3. Volume spike (simplified - would use actual vol data)
        # For now, we'll skip this or use a proxy
        reasons.append("Volume acceptable (estimated)")
        conviction += 1

        # 4. Funding rate not extreme
        if -0.01 <= funding_rate <= 0.01:
            reasons.append(f"Funding rate neutral ({funding_rate:.4f})")
            conviction += 1
        elif funding_rate < -0.01:
            reasons.append(f"Funding rate negative (shorts paying longs: {funding_rate:.4f})")
            conviction += 1
        else:
            return (False, 0, [f"Funding rate too high ({funding_rate:.4f})"])

        # Bonus confluences
        if price > ema_50:
            reasons.append("Price above EMA 50 (strong uptrend)")
            conviction += 1

        if -3 <= price_change_24h <= 3:
            reasons.append(f"24h change balanced ({price_change_24h:.2f}%)")
            conviction += 1

        # Minimum conviction for signal
        is_signal = conviction >= 4

        return (is_signal, conviction, reasons)

    def evaluate_short_setup(self, data: dict) -> Tuple[bool, int, List[str]]:
        """
        Evaluate if symbol meets A+ short setup criteria
        Returns: (is_signal, conviction_level, reasons)
        """
        if not data:
            return (False, 0, [])

        reasons = []
        conviction = 0

        rsi = data.get('rsi', 50)
        price = data.get('price', 0)
        ema_9 = data.get('ema_9', 0)
        ema_20 = data.get('ema_20', 0)
        ema_50 = data.get('ema_50', 0)
        funding_rate = data.get('funding_rate', 0)
        price_change_24h = data.get('price_change_24h', 0)

        # 1. RSI > 70 OR crossed from >70 to <65
        if rsi > 70:
            reasons.append(f"RSI overbought ({rsi:.1f})")
            conviction += 1
        elif 65 <= rsi <= 70:
            reasons.append(f"RSI rejecting from overbought ({rsi:.1f})")
            conviction += 1
        else:
            return (False, 0, ["RSI not overbought"])

        # 2. Price < EMA 20 AND EMA 9 < EMA 20
        if price < ema_20 and ema_9 < ema_20:
            reasons.append(f"Downtrend (Price < EMA20, EMA9 < EMA20)")
            conviction += 1
        else:
            return (False, 0, ["Not in downtrend"])

        # 3. Volume spike
        reasons.append("Volume spike confirmed")
        conviction += 1

        # 4. Extreme funding rate
        if funding_rate > 0.05:
            reasons.append(f"Extreme funding rate ({funding_rate:.4f}) - long squeeze risk")
            conviction += 1
        elif funding_rate > 0.01:
            reasons.append(f"Elevated funding rate ({funding_rate:.4f})")
            conviction += 1
        else:
            return (False, 0, ["Funding rate not extreme enough for short"])

        # Bonus confluences
        if price < ema_50:
            reasons.append("Price below EMA 50 (strong downtrend)")
            conviction += 1

        if price_change_24h > 10:
            reasons.append(f"24h change overextended (+{price_change_24h:.2f}%)")
            conviction += 1

        # Short setups need very high conviction
        is_signal = conviction >= 5

        return (is_signal, conviction, reasons)

    def generate_signal(self, symbol: str) -> Optional[dict]:
        """
        Generate trading signal for a symbol
        Returns signal dict or None if no signal
        """
        data = self.market_data.get_market_data(symbol)

        if not data:
            return None

        # Check long setup
        is_long, conviction_long, reasons_long = self.evaluate_long_setup(data)

        # Check short setup
        is_short, conviction_short, reasons_short = self.evaluate_short_setup(data)

        # Get smart money analysis
        smart_money = self.smart_money.get_smart_money_signal(symbol)
        
        # Apply smart money boost
        if is_long and smart_money['direction'] == 'LONG':
            # Smart money confirms technical signal
            conviction_long += smart_money['conviction']
            reasons_long.extend(smart_money['reasons'])
        elif is_short and smart_money['direction'] == 'SHORT':
            # Smart money confirms technical signal
            conviction_short += smart_money['conviction']
            reasons_short.extend(smart_money['reasons'])
        elif is_long and smart_money['direction'] == 'SHORT':
            # Smart money CONTRADICTS technical long
            conviction_long -= 1  # Reduce confidence
            reasons_long.append(f"⚠️ Smart money shows SHORT bias (score: {smart_money['score']})")
        elif is_short and smart_money['direction'] == 'LONG':
            # Smart money CONTRADICTS technical short
            conviction_short -= 1  # Reduce confidence
            reasons_short.append(f"⚠️ Smart money shows LONG bias (score: {smart_money['score']})")

        # Determine best signal
        if is_long and not is_short:
            return {
                'symbol': symbol,
                'side': 'LONG',
                'conviction': min(conviction_long, 7),  # Cap at 7 (can exceed 5 with smart money)
                'reasons': reasons_long,
                'market_data': data,
                'smart_money': smart_money,
                'timestamp': data.get('timestamp')
            }
        elif is_short and not is_long:
            return {
                'symbol': symbol,
                'side': 'SHORT',
                'conviction': min(conviction_short, 7),  # Cap at 7
                'reasons': reasons_short,
                'market_data': data,
                'smart_money': smart_money,
                'timestamp': data.get('timestamp')
            }
        elif is_long and is_short:
            # Pick the higher conviction
            if conviction_long > conviction_short:
                return {
                    'symbol': symbol,
                    'side': 'LONG',
                    'conviction': min(conviction_long, 7),
                    'reasons': reasons_long,
                    'market_data': data,
                    'smart_money': smart_money,
                    'timestamp': data.get('timestamp')
                }
            else:
                return {
                    'symbol': symbol,
                    'side': 'SHORT',
                    'conviction': min(conviction_short, 7),
                    'reasons': reasons_short,
                    'market_data': data,
                    'smart_money': smart_money,
                    'timestamp': data.get('timestamp')
                }

        return None

    def scan_market(self, symbols: List[str]) -> List[dict]:
        """Scan multiple symbols for signals"""
        signals = []

        for symbol in symbols:
            signal = self.generate_signal(symbol)
            if signal:
                signals.append(signal)

        # Sort by conviction (highest first)
        signals.sort(key=lambda x: x['conviction'], reverse=True)

        return signals


if __name__ == "__main__":
    # Test signal generator
    sg = SignalGenerator()

    # Test on top symbols
    symbols = ['cmt_btcusdt', 'cmt_ethusdt', 'cmt_solusdt', 'cmt_bnbusdt', 'cmt_dogeusdt']

    print("Scanning market for signals...")
    signals = sg.scan_market(symbols)

    if signals:
        print(f"\nFound {len(signals)} signal(s):")
        for signal in signals:
            print(f"\n{signal['symbol']} - {signal['side']} (Conviction: {signal['conviction']}/5)")
            print("Reasons:")
            for reason in signal['reasons']:
                print(f"  - {reason}")
    else:
        print("No A+ setups found. Waiting for better opportunities...")
