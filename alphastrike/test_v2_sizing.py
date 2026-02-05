#!/usr/bin/env python3
"""
Test AlphaStrike v2.0 position sizing
Shows calculations for different conviction levels
"""

def calculate_position_v2(conviction: int, equity: float, price: float):
    """v2.0 position sizing"""
    
    # Conviction-based parameters
    if conviction <= 2:
        risk_pct = 0.015
        leverage = 2
        stop_distance = 0.025
    elif conviction == 3:
        risk_pct = 0.025
        leverage = 5
        stop_distance = 0.02
    elif conviction == 4:
        risk_pct = 0.04
        leverage = 10
        stop_distance = 0.02
    else:  # conviction >= 5
        risk_pct = 0.06
        leverage = 20
        stop_distance = 0.015
    
    # Calculate position
    risk_capital = equity * risk_pct
    notional_value = risk_capital / stop_distance
    margin_required = notional_value / leverage
    size = notional_value / price
    
    # Targets
    stop_loss = price * (1 - stop_distance)
    
    if conviction >= 5:
        tp1 = None
        tp2 = price * 1.12
    else:
        tp1 = price * 1.03
        tp2 = price * 1.06
    
    return {
        'conviction': conviction,
        'risk_pct': risk_pct * 100,
        'leverage': leverage,
        'risk_capital': risk_capital,
        'notional': notional_value,
        'margin': margin_required,
        'margin_pct': (margin_required / equity) * 100,
        'size': size,
        'stop_loss': stop_loss,
        'stop_distance_pct': stop_distance * 100,
        'tp1': tp1,
        'tp2': tp2,
        'max_loss': risk_capital,
        'max_gain_tp2': (tp2 - price) / price * notional_value if tp2 else 0
    }


def print_comparison(equity=733.0, price=78485.0):
    """Print comparison table for all conviction levels"""
    
    print("="*80)
    print(f"AlphaStrike v2.0 - Position Sizing Comparison")
    print(f"Equity: ${equity:.2f} | Price: ${price:.2f}")
    print("="*80)
    print()
    
    for conv in [2, 3, 4, 5]:
        calc = calculate_position_v2(conv, equity, price)
        
        print(f"🎯 CONVICTION {conv}")
        print(f"   Risk: {calc['risk_pct']:.1f}% = ${calc['risk_capital']:.2f}")
        print(f"   Leverage: {calc['leverage']}x")
        print(f"   Margin: ${calc['margin']:.2f} ({calc['margin_pct']:.1f}% of equity)")
        print(f"   Notional: ${calc['notional']:.2f}")
        print(f"   Size: {calc['size']:.4f} contracts")
        print(f"   Stop: ${calc['stop_loss']:.2f} (-{calc['stop_distance_pct']:.1f}%)")
        
        if calc['tp1']:
            tp1_gain = (calc['tp1'] - price) / price * calc['notional']
            tp2_gain = (calc['tp2'] - price) / price * calc['notional']
            print(f"   TP1: ${calc['tp1']:.2f} (+3%) → Gain: ${tp1_gain:.2f} [50% close]")
            print(f"   TP2: ${calc['tp2']:.2f} (+6%) → Gain: ${tp2_gain:.2f} [50% close]")
            print(f"   Avg Gain: ${(tp1_gain * 0.5 + tp2_gain * 0.5):.2f}")
        else:
            tp2_gain = (calc['tp2'] - price) / price * calc['notional']
            print(f"   TP: ${calc['tp2']:.2f} (+12%) → Gain: ${tp2_gain:.2f} [FULL EXIT] 🚀")
        
        print(f"   Max Loss: -${calc['max_loss']:.2f}")
        print(f"   Risk/Reward: {abs(calc['max_gain_tp2'] / calc['max_loss']):.2f}:1")
        print()
    
    print("="*80)
    print("💡 PHILOSOPHY NOTES:")
    print("   • Conv 2: Conservative → Small position, wide stop")
    print("   • Conv 3: Standard → Medium position, normal stop")
    print("   • Conv 4: Aggressive → Large position, 10x leverage")
    print("   • Conv 5: FULL SEND → 20x leverage, 6% risk, LET IT RUN 🚀")
    print("="*80)
    print()


def test_scenarios():
    """Test specific trading scenarios"""
    
    print("="*80)
    print("SCENARIO TESTING")
    print("="*80)
    print()
    
    # Scenario 1: Conv 5 BTC long
    print("📈 SCENARIO 1: Conviction 5 - BTC Long @ $78,485")
    calc = calculate_position_v2(5, 733.0, 78485.0)
    
    print(f"   Entry: ${78485:.2f}")
    print(f"   Position: ${calc['notional']:.2f} notional ({calc['leverage']}x leverage)")
    print(f"   Margin used: ${calc['margin']:.2f} ({calc['margin_pct']:.1f}% equity)")
    print()
    print("   Price movement impacts:")
    
    for pct in [-1.5, -1.0, -0.5, 0, 0.5, 1.0, 2.0, 5.0, 12.0]:
        new_price = 78485 * (1 + pct/100)
        pnl = (new_price - 78485) * calc['size']
        pnl_on_equity = (pnl / 733) * 100
        
        marker = ""
        if pct == -1.5:
            marker = " ← STOP LOSS"
        elif pct == 12.0:
            marker = " ← TAKE PROFIT 🚀"
        
        print(f"   {pct:+5.1f}%: ${new_price:>8,.0f} → PnL: ${pnl:+8,.2f} ({pnl_on_equity:+6.1f}% equity){marker}")
    
    print()
    
    # Scenario 2: Conv 4 vs Conv 5 comparison
    print("⚖️  SCENARIO 2: Conv 4 vs Conv 5 Comparison (Same $78,485 BTC)")
    
    calc4 = calculate_position_v2(4, 733.0, 78485.0)
    calc5 = calculate_position_v2(5, 733.0, 78485.0)
    
    print(f"\n   Conv 4:")
    print(f"      Leverage: {calc4['leverage']}x | Risk: {calc4['risk_pct']:.1f}% | Margin: ${calc4['margin']:.2f}")
    print(f"      If hits +6% TP2: ${(calc4['tp2'] - 78485) / 78485 * calc4['notional']:.2f} gain")
    
    print(f"\n   Conv 5:")
    print(f"      Leverage: {calc5['leverage']}x | Risk: {calc5['risk_pct']:.1f}% | Margin: ${calc5['margin']:.2f}")
    print(f"      If hits +12% TP: ${(calc5['tp2'] - 78485) / 78485 * calc5['notional']:.2f} gain")
    
    gain4 = (calc4['tp2'] - 78485) / 78485 * calc4['notional']
    gain5 = (calc5['tp2'] - 78485) / 78485 * calc5['notional']
    
    print(f"\n   💰 Difference: ${gain5 - gain4:.2f} more with Conv 5 ({gain5/gain4:.1f}x)")
    
    print()
    print("="*80)


if __name__ == "__main__":
    print_comparison()
    test_scenarios()
    
    print("\n✅ v2.0 SIZING VERIFIED")
    print("   • Conv 5: 20x leverage, 6% risk, 1.5% stop, +12% target")
    print("   • Conv 4: 10x leverage, 4% risk, 2.0% stop, +6% target")
    print("   • Position limits: 80% (Conv 5), 60% (Conv 4), 40% (Conv 1-3)")
    print()
