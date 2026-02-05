#!/bin/bash
# Quick ADA risk check for cron

RESPONSE=$(curl -s "https://api-contract.weex.com/capi/v2/market/ticker?symbol=cmt_adausdt")
CURRENT_PRICE=$(echo "$RESPONSE" | jq -r '.last')
MARK_PRICE=$(echo "$RESPONSE" | jq -r '.markPrice')

LIQUIDATION_PRICE="0.2793"
ALERT_THRESHOLD="0.2820"

if [ -z "$CURRENT_PRICE" ] || [ "$CURRENT_PRICE" == "null" ]; then
    exit 0
fi

# Check if price is in danger zone
if (( $(echo "$CURRENT_PRICE < $ALERT_THRESHOLD" | bc -l) )); then
    DISTANCE=$(echo "scale=2; (($CURRENT_PRICE - $LIQUIDATION_PRICE) / $CURRENT_PRICE) * 100" | bc -l)
    echo "ALERT|ADA at \$$CURRENT_PRICE (mark: \$$MARK_PRICE) - Only ${DISTANCE}% from liquidation (\$$LIQUIDATION_PRICE)! Consider adding margin or closing position."
    exit 1
else
    echo "OK|ADA at \$$CURRENT_PRICE - Safe distance from liquidation"
    exit 0
fi
