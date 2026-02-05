#!/bin/bash
# Run AlphaStrike v2.0 in simulation mode
# This runs alongside the live v1.0 bot for comparison

cd "$(dirname "$0")"

echo "Starting AlphaStrike v2.0 SIMULATION..."
echo "This will run in parallel with the live v1.0 bot"
echo "Logs: alphastrike/logs/simulation_v2_$(date +%Y%m%d).log"
echo ""

# Set up environment
export WEEX_API_KEY=weex_b312cd202f9e97dde056693413959964
export WEEX_API_SECRET=8c83020575dfe348749b3269898b37b4ff03ce511413a69577817dd07c8b254d
export WEEX_PASSPHRASE=weex89769876976
export WEEX_BASE_URL=https://api-contract.weex.com

# Run in simulation mode with notifications
# Use separate state file to not conflict with live bot
python3 alphastrike.py \
    --interval 5 \
    --notify \
    2>&1 | tee -a "logs/simulation_v2_$(date +%Y%m%d).log"
