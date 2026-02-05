#!/bin/bash
# Gateway startup script for new machine
# Handles crashes and restarts

export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env)"

cd /media/DATA/clawd

while true; do
    echo "$(date): Starting gateway..."
    NODE_OPTIONS="--unhandled-rejections=warn" clawdbot gateway >> /media/DATA/clawd/gateway.log 2>&1
    
    EXIT_CODE=$?
    echo "$(date): Gateway exited with code $EXIT_CODE" >> /media/DATA/clawd/gateway.log
    
    # If clean exit (0), don't restart
    if [ $EXIT_CODE -eq 0 ]; then
        echo "$(date): Clean exit, stopping restart loop"  >> /media/DATA/clawd/gateway.log
        break
    fi
    
    # Wait 5 seconds before restart
    sleep 5
done
