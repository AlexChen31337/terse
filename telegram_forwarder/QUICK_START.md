# Quick Start Guide

## 🚀 Get Your Bot Running in 5 Minutes

### Step 1: Create Your Bot (1 minute)

1. Open Telegram, search for **@BotFather**
2. Send: `/newbot`
3. Name your bot (e.g., "My Forwarder")
4. Choose a username (e.g., "my_forwarder_bot")
5. **Copy the token** (looks like: `123456789:ABCdefGhIJK...`)

### Step 2: Get Your User ID (30 seconds)

1. Search for **@userinfobot** in Telegram
2. Send: `/start`
3. **Copy your numeric ID** (for you: `2069029798`)

### Step 3: Get Channel IDs (2 minutes)

For each channel you want to forward from:

1. Add your bot to the channel as **administrator**
2. Post a test message in the channel
3. Forward that message to **@getidsbot** (or check via Telegram API)
4. **Copy the channel ID** (negative number like: `-1001234567890`)

Repeat for all channels you want to monitor.

### Step 4: Configure (1 minute)

```bash
cd /home/bowen/.openclaw/workspace/telegram_forwarder
nano .env
```

Add your credentials:
```env
BOT_TOKEN=your_bot_token_here
OWNER_ID=2069029798
CHANNELS_TO_FORWARD=-1001234567890,-1009876543210
```

Save and exit (Ctrl+X, Y, Enter).

### Step 5: Run (30 seconds)

```bash
./setup.sh
# OR manually:
uv run python forwarder.py
```

### Step 6: Test (30 seconds)

1. Open your bot in Telegram
2. Send: `/start`
3. You should see: "🤖 Telegram Forwarder Bot Active!"
4. Send: `/health`
5. Post a test message in one of your monitored channels
6. Check that you receive a forwarded message in your private chat

## 🎯 Common Commands

Once running:
- `/stats` - See how many messages forwarded
- `/list` - See all monitored channels
- `/add -1001234567890` - Add a new channel
- `/remove -1001234567890` - Stop monitoring a channel
- `/health` - Check bot is working

## 🔧 Troubleshooting

**"Unauthorized" error:**
- Check OWNER_ID in `.env` is correct
- Ensure you're messaging from the correct account

**No messages forwarding:**
- Check bot is admin in the channel
- Verify channel IDs are correct (must be negative for channels)
- Use `/list` to see what's being monitored
- Check `forwarder.log` for errors

**Bot crashes:**
- Check `forwarder.log` for error details
- Ensure BOT_TOKEN is correct (no extra spaces)
- Verify all dependencies are installed: `uv pip install -r requirements.txt`

## 📊 What Gets Forwarded

For each message, you'll receive:
- ✅ Source channel name and link
- ✅ Message text
- ✅ Media info (photos, videos, documents)
- ✅ Timestamp
- ✅ Forward info (if message was forwarded)
- ✅ Attachments (when possible)

## 🔒 Security Notes

- Only YOU (owner ID 2069029798) can control the bot
- Other users will receive "Unauthorized" message
- Bot token is secret - never share it
- Bot logs to `forwarder.log` - check this for debugging

## 🎉 Success!

Your bot is now running and forwarding messages. Check your Telegram private chat with the bot for all forwarded messages!

## Need Help?

Check the full README.md for detailed documentation, or review the code in forwarder.py - it's well-commented!
