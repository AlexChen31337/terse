#!/bin/bash
# ADA Position Monitor - Alert if price drops to danger zone

export WEEX_API_KEY="weex_b312cd202f9e97dde056693413959964"
export WEEX_API_SECRET="8c83020575dfe348749b3269898b37b4ff03ce511413a69577817dd07c8b254d"
export WEEX_PASSPHRASE="weex89769876976"
export WEEX_BASE_URL="https://api-contract.weex.com"

TELEGRAM_CHAT_ID="2069029798"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"

ALERT_THRESHOLD="0.2820"  # Alert if price drops to $0.2820 (closer to liquidation)
LIQUIDATION_PRICE="0.2793"

while true; do
    # Get current ADA price
    RESPONSE=$(curl -s "https://api-contract.weex.com/capi/v2/market/ticker?symbol=cmt_adausdt")
    CURRENT_PRICE=$(echo "$RESPONSE" | jq -r '.last')
    MARK_PRICE=$(echo "$RESPONSE" | jq -r '.markPrice')
    
    if [ -z "$CURRENT_PRICE" ] || [ "$CURRENT_PRICE" == "null" ]; then
        echo "$(date): Failed to fetch price"
        sleep 60
        continue
    fi
    
    echo "$(date): ADA Price: $CURRENT_PRICE | Mark: $MARK_PRICE | Alert: $ALERT_THRESHOLD | Liq: $LIQUIDATION_PRICE"
    
    # Check if price is below alert threshold
    if (( $(echo "$CURRENT_PRICE < $ALERT_THRESHOLD" | bc -l) )); then
        DISTANCE_TO_LIQ=$(echo "scale=4; (($CURRENT_PRICE - $LIQUIDATION_PRICE) / $CURRENT_PRICE) * 100" | bc -l)
        
        MESSAGE="🚨 ADA DANGER ZONE!
        
Current Price: \$$CURRENT_PRICE
Mark Price: \$$MARK_PRICE
Liquidation: \$$LIQUIDATION_PRICE
Distance: ${DISTANCE_TO_LIQ}%

Your position is getting close to liquidation!"
        
        # Send Telegram alert (if bot token available)
        if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
            curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
                -d "chat_id=${TELEGRAM_CHAT_ID}" \
                -d "text=${MESSAGE}" \
                -d "parse_mode=HTML" > /dev/null
        fi
        
        echo "ALERT SENT: Price at $CURRENT_PRICE"
    fi
    
    # Check every 2 minutes
    sleep 120
done
