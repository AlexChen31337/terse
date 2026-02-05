# AlphaStrike Notifications Guide

## Overview

AlphaStrike now sends **real-time Telegram notifications** for every trade and **daily summary reports**.

## Setup

### 1. Get Your Telegram Chat ID

1. Open Telegram and search for `@userinfobot`
2. Send it any message (e.g., `/start`)
3. It will reply with your Chat ID (a number, e.g., `123456789`)
4. Copy that number

### 2. Configure AlphaStrike

```bash
cd /home/peter/clawd/alphastrike
python3 setup_notifications.py
```

Or manually set the environment variable:

```bash
export TELEGRAM_CHAT_ID='123456789'
```

### 3. Test Notifications

```bash
# Send a test message
clawdbot message send --channel telegram --target YOUR_CHAT_ID --message "Test notification"
```

## What You'll Receive

### 🚨 Real-Time Trade Alerts

**When a trade is opened:**
```
🟢 AlphaStrike: LONG Position Opened

Symbol: cmt_btcusdt
Size: 0.0500 contracts
Entry: $78,205.30
Leverage: 5x
Risk: 3.0% of equity
Conviction: 5/5

🎯 Targets:
  TP1: $80,551.46 (+3%)
  TP2: $82,897.62 (+6%)
  SL: $76,392.48 (-2.31%)

📊 Analysis:
  • RSI < 30 (oversold)
  • Price > EMA 20 (bullish momentum)
  • Volume spike 1.8x average
  • Funding rate neutral

📈 Indicators:
  RSI: 25.3
  EMA Short: 77,500
  EMA Long: 79,200
  Volume Ratio: 1.8x
  Funding Rate: 0.01%
```

**When a trade is closed:**
```
✅ AlphaStrike: LONG Position Closed

Symbol: cmt_btcusdt
Entry: $78,205.30
Exit: $80,551.46
Size: 0.0500 contracts
Reason: TP1 (50%)

💰 P&L: +58.63 USDT (+3.00%)
Hold Time: 4.2h
```

### 📊 Daily Summary Reports

Every night at 11 PM, you'll receive:
```
📊 AlphaStrike Daily Report
2026-02-01

💰 Account:
  Equity: $791.63
  Daily P&L: +58.63 USDT
  Total P&L: +58.63 USDT

📈 Performance:
  Trades Opened: 1
  Trades Closed: 1
  Wins: 1
  Losses: 0
  Win Rate: 100.0%

📝 Trade Log:
  🟢 09:15 | cmt_btcusdt LONG @ $78,205.30 | Conviction: 5/5
  ✅ 13:22 | cmt_btcusdt LONG closed @ $80,551.46 | +58.63 (+3.00%) | TP1 (50%)
```

## Running AlphaStrike with Notifications

### Enable Notifications (Default)
```bash
cd /home/peter/clawd/alphastrike

# Simulation mode
python3 alphastrike.py --once

# Live mode (real money!)
python3 alphastrike.py --live
```

### Disable Notifications
```bash
python3 alphastrike.py --no-notify
```

## Notification Types

| Event | Notification |
|-------|--------------|
| Trade Opened | ✅ Instant |
| TP1 Hit (50% close) | ✅ Instant |
| TP2 Hit (100% close) | ✅ Instant |
| Stop Loss Hit | ✅ Instant |
| Daily Summary | ✅ 11 PM daily |

## Troubleshooting

### Not receiving notifications?

1. **Check Chat ID is correct:**
   ```bash
   cat /home/peter/clawd/alphastrike/.env
   # Should show: TELEGRAM_CHAT_ID=your_number
   ```

2. **Test Clawdbot Telegram:**
   ```bash
   clawdbot channels login
   # Check Telegram is connected
   ```

3. **Test manual message:**
   ```bash
   clawdbot message send --channel telegram --target YOUR_CHAT_ID --message "Test"
   ```

### Want to change notification frequency?

Edit `alphastrike.py`:
- Change daily summary time (line with `now.hour == 23`)
- Add partial close notifications (disabled by default)
- Add custom alerts

## Privacy & Security

- Notifications contain trade details but **never** API keys
- Only your Chat ID can see your notifications
- All data transmitted via encrypted Telegram API
- WEEX AI logs stored on WEEX servers (compliance)

## Best Practices

1. **Keep notifications enabled** - Stay informed about your account
2. **Review daily summaries** - Track performance over time
3. **Act on stop-loss alerts** - Protect your capital
4. **Don't trade on emotions** - Let the strategy work

## Support

If you have issues:
1. Check `/home/peter/clawd/alphastrike/alphastrike.log`
2. Verify Telegram is connected: `clawdbot channels login`
3. Re-run setup: `python3 setup_notifications.py`

---

**Ready to trade with full transparency?** 🚀

```bash
cd /home/peter/clawd/alphastrike
python3 alphastrike.py --once  # Test in simulation
```
