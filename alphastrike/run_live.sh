#!/bin/bash
# AlphaStrike Live Trading Launcher

export WEEX_API_KEY="weex_b312cd202f9e97dde056693413959964"
export WEEX_API_SECRET="8c83020575dfe348749b3269898b37b4ff03ce511413a69577817dd07c8b254d"
export WEEX_PASSPHRASE="weex89769876976"
export WEEX_BASE_URL="https://api-contract.weex.com"
export TELEGRAM_CHAT_ID="2069029798"

cd /home/peter/clawd/alphastrike
python3 alphastrike.py --live --interval 5 "$@"
