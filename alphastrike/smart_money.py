#!/usr/bin/env python3
"""
Smart Money Tracking Module for AlphaStrike
Tracks whale movements, large orders, and institutional flow

Signals to track:
1. Large liquidations (cascade opportunities)
2. Whale wallet movements (on-chain)
3. Exchange inflow/outflow (selling/buying pressure)
4. Funding rate extremes (overleveraged positions)
5. Open Interest changes (new positions opening)
6. Order book imbalances (large bids/asks)
7. CVD (Cumulative Volume Delta) - buy vs sell pressure
"""

import os
import sys
import time
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

# Add parent directory to path to import weex_client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../.clawdbot/skills/weex-trading'))
from weex_client import WeexClient


class SmartMoneyTracker:
    """Track smart money movements and whale activity"""

    def __init__(self):
        self.client = WeexClient()
        self.cache = {}
        self.cache_ttl = 60  # Cache for 60 seconds

    def _get_cached(self, key: str) -> Optional[dict]:
        """Get cached data if still valid"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return data
        return None

    def _set_cache(self, key: str, data: dict):
        """Cache data with timestamp"""
        self.cache[key] = (data, time.time())

    # ============================================================================
    # 1. FUNDING RATE EXTREMES
    # ============================================================================

    def check_funding_extreme(self, symbol: str) -> Tuple[bool, str, float]:
        """
        Check if funding rate is at extreme levels
        
        Returns: (is_extreme, signal_type, funding_rate)
        - signal_type: "LONG" (shorts overleveraged) or "SHORT" (longs overleveraged)
        """
        try:
            result = self.client.get_funding_rate(symbol)
            
            if not result or 'data' not in result:
                return (False, None, 0.0)
            
            for item in result['data']:
                if item['symbol'] == symbol:
                    funding_rate = float(item.get('fundingRate', 0))
                    
                    # Negative funding = shorts pay longs (bearish sentiment)
                    # → Contrarian LONG signal
                    if funding_rate < -0.05:
                        return (True, "LONG", funding_rate)
                    elif funding_rate < -0.02:
                        return (True, "LONG_WEAK", funding_rate)
                    
                    # Positive funding = longs pay shorts (bullish sentiment)
                    # → Contrarian SHORT signal (overheated)
                    elif funding_rate > 0.10:
                        return (True, "SHORT", funding_rate)
                    elif funding_rate > 0.05:
                        return (True, "SHORT_WEAK", funding_rate)
            
            return (False, None, 0.0)
            
        except Exception as e:
            print(f"Error checking funding rate for {symbol}: {e}")
            return (False, None, 0.0)

    # ============================================================================
    # 2. OPEN INTEREST ANALYSIS
    # ============================================================================

    def check_open_interest_change(self, symbol: str) -> Tuple[bool, str, float]:
        """
        Check if Open Interest is changing significantly
        
        Rising OI + Rising Price = Strong uptrend (new longs entering)
        Rising OI + Falling Price = Strong downtrend (new shorts entering)
        Falling OI + Rising Price = Short squeeze
        Falling OI + Falling Price = Long liquidations
        
        Returns: (is_signal, signal_type, oi_change_pct)
        """
        # Note: WEEX API may not provide OI history
        # This is a framework - implement when API endpoint available
        
        # Placeholder implementation
        return (False, None, 0.0)

    # ============================================================================
    # 3. ORDER BOOK IMBALANCE
    # ============================================================================

    def check_orderbook_imbalance(self, symbol: str, depth: int = 20) -> Tuple[bool, str, float]:
        """
        Check for large buy/sell walls in order book
        
        Large bid wall = Support (smart money accumulating)
        Large ask wall = Resistance (smart money distributing)
        
        Returns: (is_signal, signal_type, imbalance_ratio)
        """
        try:
            result = self.client.get_depth(symbol, depth)
            
            if not result or 'data' not in result:
                return (False, None, 0.0)
            
            data = result['data']
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            
            if not bids or not asks:
                return (False, None, 0.0)
            
            # Calculate total bid/ask volume (top 20 levels)
            bid_volume = sum(float(bid[1]) for bid in bids[:depth])
            ask_volume = sum(float(ask[1]) for ask in asks[:depth])
            
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return (False, None, 0.0)
            
            # Imbalance ratio
            bid_ratio = bid_volume / total_volume
            ask_ratio = ask_volume / total_volume
            
            # Strong bid support (70%+ bids)
            if bid_ratio > 0.70:
                return (True, "LONG", bid_ratio)
            elif bid_ratio > 0.60:
                return (True, "LONG_WEAK", bid_ratio)
            
            # Strong ask resistance (70%+ asks)
            elif ask_ratio > 0.70:
                return (True, "SHORT", ask_ratio)
            elif ask_ratio > 0.60:
                return (True, "SHORT_WEAK", ask_ratio)
            
            return (False, None, bid_ratio)
            
        except Exception as e:
            print(f"Error checking orderbook for {symbol}: {e}")
            return (False, None, 0.0)

    # ============================================================================
    # 4. CUMULATIVE VOLUME DELTA (CVD)
    # ============================================================================

    def check_volume_delta(self, symbol: str) -> Tuple[bool, str, float]:
        """
        Check Cumulative Volume Delta (buy volume vs sell volume)
        
        Positive CVD = More buying pressure (bullish)
        Negative CVD = More selling pressure (bearish)
        
        Price up + CVD down = Divergence (weak move, likely reversal)
        Price down + CVD up = Divergence (accumulation, likely bounce)
        
        Returns: (is_signal, signal_type, cvd_ratio)
        """
        # Note: Need trade history to calculate CVD
        # Fetch recent trades and classify as buy/sell based on side
        
        try:
            # Get recent trades
            result = self.client.get_trades(symbol, limit=100)
            
            if not result or 'data' not in result:
                return (False, None, 0.0)
            
            trades = result['data']
            
            buy_volume = 0.0
            sell_volume = 0.0
            
            for trade in trades:
                volume = float(trade.get('size', 0))
                side = trade.get('side', '').lower()
                
                # Classify as buy/sell
                # If 'side' == 'buy', it's a market buy (taker buy = bullish)
                # If 'side' == 'sell', it's a market sell (taker sell = bearish)
                if side == 'buy':
                    buy_volume += volume
                elif side == 'sell':
                    sell_volume += volume
            
            total_volume = buy_volume + sell_volume
            if total_volume == 0:
                return (False, None, 0.0)
            
            # CVD ratio
            cvd_ratio = (buy_volume - sell_volume) / total_volume
            
            # Strong buying pressure
            if cvd_ratio > 0.3:
                return (True, "LONG", cvd_ratio)
            elif cvd_ratio > 0.15:
                return (True, "LONG_WEAK", cvd_ratio)
            
            # Strong selling pressure
            elif cvd_ratio < -0.3:
                return (True, "SHORT", cvd_ratio)
            elif cvd_ratio < -0.15:
                return (True, "SHORT_WEAK", cvd_ratio)
            
            return (False, None, cvd_ratio)
            
        except Exception as e:
            print(f"Error checking volume delta for {symbol}: {e}")
            return (False, None, 0.0)

    # ============================================================================
    # 5. LIQUIDATION TRACKING
    # ============================================================================

    def check_liquidations(self, symbol: str) -> Tuple[bool, str, float]:
        """
        Track large liquidations
        
        Large long liquidations = Cascade selling (wait for bottom, then LONG)
        Large short liquidations = Short squeeze (momentum, join LONG)
        
        Returns: (is_signal, signal_type, liquidation_volume)
        """
        # Note: WEEX may not provide liquidation data via API
        # Alternative: Use external services like Coinglass API
        
        # Placeholder for external liquidation data
        # In production, integrate with Coinglass or similar
        
        return (False, None, 0.0)

    # ============================================================================
    # 6. WHALE WALLET TRACKING (On-Chain)
    # ============================================================================

    def check_whale_movements(self, symbol: str) -> Tuple[bool, str, float]:
        """
        Track large on-chain movements
        
        Whale deposits to exchange = Potential sell pressure
        Whale withdrawals from exchange = Accumulation (bullish)
        
        Returns: (is_signal, signal_type, net_flow)
        """
        # Note: Requires on-chain data APIs (Glassnode, Nansen, etc.)
        # Not available via WEEX API
        
        # Placeholder - would require external API integration
        
        return (False, None, 0.0)

    # ============================================================================
    # AGGREGATE SMART MONEY SIGNAL
    # ============================================================================

    def get_smart_money_signal(self, symbol: str) -> dict:
        """
        Aggregate all smart money indicators
        
        Returns comprehensive smart money analysis
        """
        signals = {
            'symbol': symbol,
            'timestamp': int(time.time()),
            'funding': {},
            'orderbook': {},
            'cvd': {},
            'score': 0,  # -5 to +5 (negative = SHORT bias, positive = LONG bias)
            'conviction': 0,  # 0-5
            'reasons': []
        }
        
        # Check funding rate
        is_extreme, funding_signal, funding_rate = self.check_funding_extreme(symbol)
        signals['funding'] = {
            'rate': funding_rate,
            'is_extreme': is_extreme,
            'signal': funding_signal
        }
        
        if is_extreme:
            if funding_signal == "LONG":
                signals['score'] += 2
                signals['conviction'] += 1
                signals['reasons'].append(f"Extreme negative funding ({funding_rate:.4f}%) - shorts overleveraged")
            elif funding_signal == "LONG_WEAK":
                signals['score'] += 1
                signals['reasons'].append(f"Negative funding ({funding_rate:.4f}%) - short bias")
            elif funding_signal == "SHORT":
                signals['score'] -= 2
                signals['conviction'] += 1
                signals['reasons'].append(f"Extreme positive funding ({funding_rate:.4f}%) - longs overleveraged")
            elif funding_signal == "SHORT_WEAK":
                signals['score'] -= 1
                signals['reasons'].append(f"High positive funding ({funding_rate:.4f}%) - long bias")
        
        # Check orderbook imbalance
        is_imbalance, ob_signal, imbalance_ratio = self.check_orderbook_imbalance(symbol)
        signals['orderbook'] = {
            'imbalance_ratio': imbalance_ratio,
            'is_imbalanced': is_imbalance,
            'signal': ob_signal
        }
        
        if is_imbalance:
            if ob_signal == "LONG":
                signals['score'] += 2
                signals['conviction'] += 1
                signals['reasons'].append(f"Strong bid support ({imbalance_ratio:.1%}) - smart money accumulating")
            elif ob_signal == "LONG_WEAK":
                signals['score'] += 1
                signals['reasons'].append(f"Bid support ({imbalance_ratio:.1%})")
            elif ob_signal == "SHORT":
                signals['score'] -= 2
                signals['conviction'] += 1
                signals['reasons'].append(f"Strong ask resistance ({imbalance_ratio:.1%}) - smart money distributing")
            elif ob_signal == "SHORT_WEAK":
                signals['score'] -= 1
                signals['reasons'].append(f"Ask resistance ({imbalance_ratio:.1%})")
        
        # Check CVD
        is_cvd_signal, cvd_signal, cvd_ratio = self.check_volume_delta(symbol)
        signals['cvd'] = {
            'ratio': cvd_ratio,
            'is_signal': is_cvd_signal,
            'signal': cvd_signal
        }
        
        if is_cvd_signal:
            if cvd_signal == "LONG":
                signals['score'] += 2
                signals['conviction'] += 1
                signals['reasons'].append(f"Strong buying pressure (CVD: {cvd_ratio:+.2%}) - taker buys dominating")
            elif cvd_signal == "LONG_WEAK":
                signals['score'] += 1
                signals['reasons'].append(f"Buying pressure (CVD: {cvd_ratio:+.2%})")
            elif cvd_signal == "SHORT":
                signals['score'] -= 2
                signals['conviction'] += 1
                signals['reasons'].append(f"Strong selling pressure (CVD: {cvd_ratio:+.2%}) - taker sells dominating")
            elif cvd_signal == "SHORT_WEAK":
                signals['score'] -= 1
                signals['reasons'].append(f"Selling pressure (CVD: {cvd_ratio:+.2%})")
        
        # Determine overall signal
        if signals['score'] >= 3:
            signals['direction'] = "LONG"
        elif signals['score'] <= -3:
            signals['direction'] = "SHORT"
        else:
            signals['direction'] = None
        
        return signals

    def scan_smart_money(self, symbols: List[str]) -> List[dict]:
        """Scan multiple symbols for smart money signals"""
        results = []
        
        for symbol in symbols:
            signal = self.get_smart_money_signal(symbol)
            
            # Only return if there's a clear signal
            if signal['direction'] and signal['conviction'] >= 1:
                results.append(signal)
        
        # Sort by conviction (highest first)
        results.sort(key=lambda x: (x['conviction'], abs(x['score'])), reverse=True)
        
        return results


def main():
    """Test smart money tracker"""
    tracker = SmartMoneyTracker()
    
    symbols = ['cmt_btcusdt', 'cmt_ethusdt', 'cmt_solusdt', 'cmt_bnbusdt', 'cmt_dogeusdt']
    
    print("="*80)
    print("SMART MONEY ANALYSIS")
    print("="*80)
    print()
    
    signals = tracker.scan_smart_money(symbols)
    
    if signals:
        print(f"Found {len(signals)} smart money signal(s):")
        print()
        
        for signal in signals:
            print(f"📊 {signal['symbol'].replace('cmt_', '').upper()}")
            print(f"   Direction: {signal['direction']}")
            print(f"   Conviction: {signal['conviction']}/5")
            print(f"   Score: {signal['score']:+d}")
            print()
            print("   Indicators:")
            print(f"   • Funding: {signal['funding']['rate']:.4f}% ({signal['funding']['signal'] or 'neutral'})")
            print(f"   • Orderbook: {signal['orderbook']['imbalance_ratio']:.1%} bid ratio ({signal['orderbook']['signal'] or 'balanced'})")
            print(f"   • CVD: {signal['cvd']['ratio']:+.2%} ({signal['cvd']['signal'] or 'neutral'})")
            print()
            print("   Reasons:")
            for reason in signal['reasons']:
                print(f"   • {reason}")
            print()
            print("-"*80)
            print()
    else:
        print("No smart money signals detected.")
        print("Market conditions: neutral / no clear institutional bias")
    
    print("="*80)


if __name__ == "__main__":
    main()
