# ✅ Setup Checklist

Follow these steps to get your Telegram bot running:

## 1. Create Your Bot ✏️

- [ ] Open Telegram and search for **@BotFather**
- [ ] Send command: `/newbot`
- [ ] Choose a name (e.g., "Message Forwarder")
- [ ] Choose a username (e.g., `my_forwarder_bot`)
- [ ] **Copy the bot token** (looks like: `123456789:ABCdefGhIJK...`)

## 2. Configure Environment Variables ⚙️

- [ ] Navigate to bot directory:
  ```bash
  cd /home/bowen/.openclaw/workspace/telegram_forwarder
  ```

- [ ] Create your `.env` file:
  ```bash
  cp .env.example .env
  nano .env
  ```

- [ ] Edit `.env` with your bot token:
  ```env
  BOT_TOKEN=your_actual_bot_token_here
  OWNER_ID=2069029798
  CHANNELS_TO_FORWARD=
  ```

- [ ] Save and exit (Ctrl+X, Y, Enter)

## 3. Install Dependencies 📦

- [ ] Run the setup script:
  ```bash
  ./setup.sh
  ```

  OR manually:
  ```bash
  uv pip install -r requirements.txt
  ```

## 4. Get Channel IDs 🔍

### Option A: Using the Helper Script

- [ ] Start the helper script:
  ```bash
  uv run python channel_id_helper.py
  ```

- [ ] Add your bot to each channel as **administrator**
- [ ] Post a message in each channel
- [ ] Copy the Chat ID from the output (negative number like `-1001234567890`)

### Option B: Using @getidsbot

- [ ] Search for **@getidsbot** in Telegram
- [ ] Start the bot: `/start`
- [ ] Forward a message from your channel to @getidsbot
- [ ] Copy the "Chat ID" (negative number)

## 5. Add Channels to .env 📝

Edit `.env` and add your channel IDs:

```env
BOT_TOKEN=your_actual_bot_token_here
OWNER_ID=2069029798
CHANNELS_TO_FORWARD=-1001234567890,-1009876543210
```

**Notes:**
- Multiple channels separated by commas
- No spaces
- Channel IDs are negative numbers

## 6. Start the Bot 🚀

- [ ] Run the bot:
  ```bash
  uv run python forwarder.py
  ```

- [ ] You should see:
  ```
  Starting Telegram Forwarder Bot...
  Owner ID: 2069029798
  Monitoring N channels: [-1001234567890, ...]
  Bot is running...
  ```

## 7. Test Your Bot ✅

- [ ] Open your bot in Telegram (search for your bot's username)
- [ ] Send: `/start`
- [ ] You should receive: "🤖 Telegram Forwarder Bot Active!"
- [ ] Send: `/health`
- [ ] You should see bot status
- [ ] Post a test message in one of your monitored channels
- [ ] Check that you receive a forwarded message in your private chat

## 8. Run as a Service (Optional) 🔄

### Using tmux

- [ ] Create tmux session:
  ```bash
  tmux new-session -d -s telegram-bot 'cd /home/bowen/.openclaw/workspace/telegram_forwarder && uv run python forwarder.py'
  ```

- [ ] Verify it's running:
  ```bash
  tmux ls
  ```

- [ ] Attach to see logs:
  ```bash
  tmux attach-session -t telegram-bot
  ```

- [ ] Detach: Press `Ctrl+B`, then `D`

## 9. Monitor and Maintain 📊

### Regular Commands

- [ ] Check stats: Send `/stats` to your bot
- [ ] List channels: Send `/list` to your bot
- [ ] Add new channel: Send `/add -1001234567890`
- [ ] Remove channel: Send `/remove -1001234567890`
- [ ] Check health: Send `/health` to your bot

### Log Files

- [ ] Check `forwarder.log` for detailed logs
- [ ] Look for errors or warnings

## Troubleshooting 🔧

### Bot doesn't respond to commands
- [ ] Check `.env` has correct BOT_TOKEN
- [ ] Verify bot is running (no errors in console)
- [ ] Ensure OWNER_ID is 2069029798

### Messages not forwarding
- [ ] Bot must be **admin** in the channel
- [ ] Check channel IDs are correct (negative numbers)
- [ ] Use `/list` command to see monitored channels
- [ ] Check `forwarder.log` for errors

### Bot crashes on startup
- [ ] Verify BOT_TOKEN (no extra spaces)
- [ ] Check dependencies installed: `uv pip list | grep telegram`
- [ ] Check Python version: `python --version` (need 3.8+)

### Unauthorized access errors
- [ ] Only you (ID: 2069029798) can use commands
- [ ] Other users will get "Unauthorized" message
- [ ] This is normal and expected behavior

## Files Created 📁

```
telegram_forwarder/
├── forwarder.py              # Main bot script (11,673 bytes)
├── channel_id_helper.py      # Helper to find channel IDs (1,947 bytes)
├── setup.sh                  # Setup script (1,186 bytes)
├── requirements.txt          # Python dependencies (62 bytes)
├── .env.example              # Config template (181 bytes)
├── .gitignore                # Git exclusions (204 bytes)
├── README.md                 # Full documentation (4,363 bytes)
├── QUICK_START.md            # 5-minute guide (3,010 bytes)
├── INSTALLATION_SUMMARY.md   # Setup summary (5,069 bytes)
└── SETUP_CHECKLIST.md        # This file
```

## Security Notes 🔒

- [ ] Never share your `.env` file or BOT_TOKEN
- [ ] Never commit `.env` to git (it's in `.gitignore`)
- [ ] Only owner (ID: 2069029798) can control the bot
- [ ] Bot logs to `forwarder.log` - check permissions

## Next Steps 🎯

Once everything is working:

1. ✅ Add all channels you want to monitor
2. ✅ Test message forwarding with real messages
3. ✅ Set up bot to run as a service (tmux or systemd)
4. ✅ Monitor logs periodically
5. ✅ Adjust channels as needed using `/add` and `/remove`

## Support 📚

- Read `QUICK_START.md` for quick setup
- Read `README.md` for full documentation
- Check `forwarder.log` for runtime issues
- Review code comments in `forwarder.py`

---

**Status:** Ready to configure and run!
**Location:** `/home/bowen/.openclaw/workspace/telegram_forwarder/`
**Owner ID:** 2069029798
