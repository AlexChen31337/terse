#!/bin/bash
# Quick status check for paper trading

STATE_FILE="/home/peter/clawd/alphastrike/state.json"

if [ ! -f "$STATE_FILE" ]; then
    echo "No paper trading session found. Start with: cd ~/clawd/alphastrike && python3 run_paper_trading.py"
    exit 1
fi

echo "AlphaStrike v2.0 Paper Trading Status"
echo "======================================"
echo ""

# Parse state.json
cat "$STATE_FILE" | jq -r '
"Equity: $" + (.equity | tostring),
"Daily P&L: $" + (.daily_pnl | tostring),
"Trades Today: " + (.trades_today | tostring) + "/2",
"Total Trades: " + (.total_trades | tostring),
"Win Rate: " + (.win_rate | tostring) + "%",
"",
"Open Positions: " + (.positions | length | tostring)
'

# Show positions if any
POSITIONS=$(cat "$STATE_FILE" | jq -r '.positions | length')
if [ "$POSITIONS" -gt 0 ]; then
    echo ""
    cat "$STATE_FILE" | jq -r '.positions[] | 
    "  • " + .symbol + ": " + .side + " " + (.size | tostring) + " @ $" + (.entry_price | tostring) + 
    " | P&L: $" + (.unrealized_pnl | tostring)'
fi

echo ""
echo "Last updated: $(stat -c %y "$STATE_FILE" | cut -d'.' -f1)"
