#!/usr/bin/env python3
"""
Compare v1.0 (live) vs v2.0 (simulation) performance
Shows what trades v2.0 would have taken with 20x leverage
"""

import json
import os
from datetime import datetime

def load_state(state_file):
    """Load bot state from JSON"""
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            return json.load(f)
    return {}

def calculate_metrics(state):
    """Calculate performance metrics"""
    if not state:
        return {
            'equity': 733.0,
            'pnl': 0.0,
            'pnl_pct': 0.0,
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0
        }
    
    equity = state.get('equity', 733.0)
    starting_equity = 733.0
    pnl = equity - starting_equity
    pnl_pct = (pnl / starting_equity) * 100
    
    history = state.get('trade_history', [])
    closed_trades = [t for t in history if t.get('status') == 'CLOSED']
    
    wins = [t for t in closed_trades if t.get('pnl', 0) > 0]
    losses = [t for t in closed_trades if t.get('pnl', 0) < 0]
    
    win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0
    avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
    
    return {
        'equity': equity,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'trades': len(closed_trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss
    }

def main():
    """Compare v1 and v2 performance"""
    
    v1_state = load_state('state.json')  # Live bot
    v2_state = load_state('state_v2.json')  # Simulation bot (if exists)
    
    v1_metrics = calculate_metrics(v1_state)
    v2_metrics = calculate_metrics(v2_state)
    
    print("="*80)
    print("AlphaStrike v1.0 (LIVE) vs v2.0 (SIMULATION) Comparison")
    print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    
    # Summary comparison
    print("📊 PERFORMANCE SUMMARY")
    print()
    print(f"{'Metric':<20} {'v1.0 (LIVE)':<20} {'v2.0 (SIM)':<20} {'Difference':<20}")
    print("-"*80)
    
    metrics = [
        ('Equity', 'equity', '${:.2f}'),
        ('P&L', 'pnl', '${:+.2f}'),
        ('P&L %', 'pnl_pct', '{:+.2f}%'),
        ('Total Trades', 'trades', '{}'),
        ('Wins', 'wins', '{}'),
        ('Losses', 'losses', '{}'),
        ('Win Rate', 'win_rate', '{:.1f}%'),
        ('Avg Win', 'avg_win', '${:.2f}'),
        ('Avg Loss', 'avg_loss', '${:.2f}'),
    ]
    
    for label, key, fmt in metrics:
        v1_val = v1_metrics[key]
        v2_val = v2_metrics[key]
        
        if key in ['equity', 'pnl', 'avg_win', 'avg_loss']:
            diff = v2_val - v1_val
            diff_str = fmt.format(diff)
        elif key == 'pnl_pct':
            diff = v2_val - v1_val
            diff_str = f"{diff:+.2f}%"
        else:
            diff = v2_val - v1_val
            diff_str = f"{diff:+.0f}"
        
        print(f"{label:<20} {fmt.format(v1_val):<20} {fmt.format(v2_val):<20} {diff_str:<20}")
    
    print()
    print("="*80)
    
    # Recent trades
    print()
    print("📈 RECENT TRADES (Last 5)")
    print()
    
    v1_recent = v1_state.get('trade_history', [])[-5:] if v1_state else []
    v2_recent = v2_state.get('trade_history', [])[-5:] if v2_state else []
    
    if v1_recent:
        print("v1.0 (LIVE):")
        for trade in v1_recent:
            ts = datetime.fromtimestamp(trade['timestamp']).strftime('%Y-%m-%d %H:%M')
            symbol = trade.get('symbol', 'N/A')
            side = trade.get('side', 'N/A')
            pnl = trade.get('pnl', 0)
            reason = trade.get('exit_reason', 'N/A')
            print(f"  {ts} | {symbol:<12} | {side:<5} | {pnl:+8.2f} | {reason}")
    else:
        print("v1.0 (LIVE): No trades yet")
    
    print()
    
    if v2_recent:
        print("v2.0 (SIMULATION):")
        for trade in v2_recent:
            ts = datetime.fromtimestamp(trade['timestamp']).strftime('%Y-%m-%d %H:%M')
            symbol = trade.get('symbol', 'N/A')
            side = trade.get('side', 'N/A')
            pnl = trade.get('pnl', 0)
            reason = trade.get('exit_reason', 'N/A')
            conv = trade.get('conviction', 'N/A')
            print(f"  {ts} | {symbol:<12} | {side:<5} | Conv {conv} | {pnl:+8.2f} | {reason}")
    else:
        print("v2.0 (SIMULATION): No trades yet")
    
    print()
    print("="*80)
    
    # Open positions
    v1_positions = v1_state.get('positions', [])
    v2_positions = v2_state.get('positions', [])
    
    print()
    print("📌 OPEN POSITIONS")
    print()
    
    if v1_positions:
        print(f"v1.0 (LIVE): {len(v1_positions)} open")
        for pos in v1_positions:
            symbol = pos.get('symbol', 'N/A')
            side = pos.get('side', 'N/A')
            entry = pos.get('entry_price', 0)
            size = pos.get('size', 0)
            leverage = pos.get('leverage', 0)
            print(f"  {symbol} {side} | Entry: ${entry:.2f} | Size: {size:.4f} | {leverage}x")
    else:
        print("v1.0 (LIVE): No open positions")
    
    print()
    
    if v2_positions:
        print(f"v2.0 (SIMULATION): {len(v2_positions)} open")
        for pos in v2_positions:
            symbol = pos.get('symbol', 'N/A')
            side = pos.get('side', 'N/A')
            entry = pos.get('entry_price', 0)
            size = pos.get('size', 0)
            leverage = pos.get('leverage', 0)
            conv = pos.get('conviction', 'N/A')
            print(f"  {symbol} {side} Conv {conv} | Entry: ${entry:.2f} | Size: {size:.4f} | {leverage}x")
    else:
        print("v2.0 (SIMULATION): No open positions")
    
    print()
    print("="*80)
    
    # Key insights
    if v2_metrics['trades'] > 0 or v1_metrics['trades'] > 0:
        print()
        print("💡 KEY INSIGHTS:")
        
        if v2_metrics['pnl'] > v1_metrics['pnl']:
            diff = v2_metrics['pnl'] - v1_metrics['pnl']
            pct = (diff / abs(v1_metrics['pnl'])) * 100 if v1_metrics['pnl'] != 0 else 999
            print(f"  • v2.0 outperforming v1.0 by ${diff:.2f} ({pct:.1f}%)")
        elif v1_metrics['pnl'] > v2_metrics['pnl']:
            diff = v1_metrics['pnl'] - v2_metrics['pnl']
            print(f"  • v1.0 outperforming v2.0 by ${diff:.2f}")
        
        if v2_metrics['trades'] > v1_metrics['trades']:
            print(f"  • v2.0 taking more trades ({v2_metrics['trades']} vs {v1_metrics['trades']})")
        
        if v2_metrics['win_rate'] > v1_metrics['win_rate']:
            diff = v2_metrics['win_rate'] - v1_metrics['win_rate']
            print(f"  • v2.0 higher win rate ({v2_metrics['win_rate']:.1f}% vs {v1_metrics['win_rate']:.1f}%)")
        
        print("="*80)
    
    print()

if __name__ == "__main__":
    main()
