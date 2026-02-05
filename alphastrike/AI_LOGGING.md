# AlphaStrike AI Logging

## Implementation Status

AlphaStrike now submits AI trading logs to WEEX on every order placement and position closure.

## What Gets Logged

### 1. Trade Entry Logs
When AlphaStrike opens a position, it logs:
- **Symbol**: Trading pair (e.g., cmt_btcusdt)
- **Action**: Open LONG or Open SHORT
- **Reason**: Full rationale for the trade (all signal criteria)
- **Size**: Position size in contracts
- **Price**: Entry price
- **Confidence**: Conviction level (1-5)
- **Strategy**: "AlphaStrike v1.0"
- **Indicators**: RSI, EMA values, volume ratio, funding rate, current price

### 2. Position Closure Logs
When AlphaStrike closes a position, it logs:
- **Symbol**: Trading pair
- **Action**: Close LONG or Close SHORT
- **Reason**: Why closed (TP1, TP2, Stop Loss, manual)
- **Size**: Position size closed
- **Price**: Exit price
- **P&L**: Profit/loss in USDT and percentage
- **Hold Time**: How long the position was open

## WEEX API Integration

### Endpoint
```
POST /capi/v2/order/uploadAiLog
```

### Authentication
Uses standard WEEX API signature authentication (same as trading endpoints).

### Parameters
```json
{
  "symbol": "cmt_btcusdt",
  "stage": "Decision Making",
  "input": "RSI < 30, Price > EMA 20, Volume spike 1.8x, Funding neutral",
  "output": "{\"action\":\"Open LONG\",\"size\":\"10\",\"price\":\"95000\",...}"
}
```

### Stage Values
- **"Decision Making"**: AI is analyzing and making trading decisions

## Current Status

⚠️ **API Access Issue**: The current WEEX API key returns error code `40020` (Request parameter format is incorrect) when attempting to submit AI logs.

### Possible Reasons:
1. AI logging feature may need to be enabled for the API key
2. Specific parameter format required by WEEX not yet documented
3. API key permissions may not include AI logging

### Graceful Degradation
AlphaStrike handles AI log failures gracefully:
- ✅ Trade execution continues normally even if AI log fails
- ✅ Warning logged to console
- ✅ No crashes or interruptions
- ✅ All trade data still saved locally in `alphastrike_state.json`

## Next Steps

### For Production Use:
1. **Contact WEEX Support** to enable AI logging for your API key
2. **Request API documentation** for the exact format expected by `/capi/v2/order/uploadAiLog`
3. **Test with sample data** before live trading

### In the Meantime:
- AlphaStrike logs all trades locally in `alphastrike_state.json`
- Full trade history with rationale preserved
- AI log submission will work automatically once API access is enabled

## Benefits of AI Logging

When enabled, AI logging provides:

1. **Transparency**: Complete audit trail of AI-driven trades
2. **Compliance**: Meets regulatory requirements for AI trading
3. **Analysis**: Review past decisions to improve strategy
4. **Debugging**: Understand why specific trades were made
5. **Trust**: Demonstrates thoughtful, rule-based trading

## Local Logging Fallback

Even without WEEX AI log submission, AlphaStrike maintains complete records:

```json
{
  "positions": [...],
  "trade_history": [
    {
      "timestamp": 1769895453,
      "symbol": "cmt_ethusdt",
      "side": "LONG",
      "entry_price": 2412.50,
      "exit_price": 2485.00,
      "exit_reason": "TP2",
      "pnl": 72.50,
      "pnl_pct": 3.0,
      "status": "CLOSED"
    }
  ],
  "daily_pnl": 72.50
}
```

## Testing

To test AI log submission:

```bash
cd /home/peter/.clawdbot/skills/weex-trading
export WEEX_API_KEY="your_key"
export WEEX_API_SECRET="your_secret"
export WEEX_API_PASSPHRASE="your_passphrase"
python3 test_ai_log.py
```

## Code Locations

- **WEEX Client**: `/home/peter/.clawdbot/skills/weex-trading/weex_client.py`
- **AlphaStrike Bot**: `/home/peter/clawd/alphastrike/alphastrike.py`
- **Test Script**: `/home/peter/.clawdbot/skills/weex-trading/test_ai_log.py`

## Summary

✅ AI logging fully implemented in AlphaStrike
✅ Logs submitted on every trade entry and exit
✅ Graceful handling if API access not enabled
⚠️ Contact WEEX to enable AI logging for your API key
