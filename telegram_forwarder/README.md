# Telegram Message Forwarder Bot

A robust Telegram bot that forwards messages from specified channels and reports results back to the owner.

## Features

- ✅ Forward messages from multiple channels
- ✅ Support for text, photos, videos, and documents
- ✅ Real-time statistics and reporting
- ✅ Owner-only commands (private bot)
- ✅ Detailed logging
- ✅ Error handling and recovery
- ✅ Health monitoring

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the prompts to name your bot
4. Copy the bot token (looks like `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`)

### 2. Get Your Telegram User ID

1. Search for [@userinfobot](https://t.me/userinfobot) in Telegram
2. Send `/start`
3. Copy your numeric user ID (should be `2069029798` for your account)

### 3. Get Channel IDs to Monitor

For each channel you want to monitor:

1. Add the bot to the channel (as admin)
2. Post a message in the channel
3. Use a Telegram API tool or forward the message to @userinfobot to see the channel ID
4. Channel IDs are usually negative numbers (e.g., `-1001234567890`)

### 4. Configure the Bot

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Add your configuration:
```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
OWNER_ID=2069029798
CHANNELS_TO_FORWARD=-1001234567890,-1009876543210
```

### 5. Install Dependencies

```bash
cd /home/bowen/.openclaw/workspace/telegram_forwarder
pip install -r requirements.txt
```

Or with uv (recommended):
```bash
uv pip install -r requirements.txt
```

### 6. Run the Bot

```bash
python forwarder.py
```

Or with uv:
```bash
uv run python forwarder.py
```

## Commands

Only the owner (user ID 2069029798) can use these commands:

- `/start` - Initialize the bot and show welcome message
- `/stats` - Show forwarding statistics (total, forwarded, errors, success rate)
- `/add <channel_id>` - Add a channel to monitor
  - Example: `/add -1001234567890`
- `/remove <channel_id>` - Remove a channel from monitoring
  - Example: `/remove -1001234567890`
- `/list` - Show all monitored channels
- `/health` - Show bot health status

## Features Detail

### Message Forwarding

The bot will:
- Capture all messages from monitored channels
- Extract text, media, and metadata
- Send a formatted report to the owner
- Include source information and timestamp
- Forward photos and documents when possible

### Error Handling

- Failed forwards are logged
- Owner is notified of errors
- Bot continues running after errors
- Detailed error logs in `forwarder.log`

### Logging

All activity is logged to:
- Console (stdout)
- `forwarder.log` file

Logs include:
- Message forwards
- Errors with stack traces
- Owner commands
- Bot status changes

## Running as a Service

### Using tmux

```bash
# Create a new tmux session
tmux new-session -d -s telegram-bot 'cd /home/bowen/.openclaw/workspace/telegram_forwarder && uv run python forwarder.py'

# Attach to session
tmux attach-session -t telegram-bot

# Detach: Ctrl+B, then D
```

### Using systemd (optional)

Create `/etc/systemd/system/telegram-forwarder.service`:

```ini
[Unit]
Description=Telegram Forwarder Bot
After=network.target

[Service]
Type=simple
User=bowen
WorkingDirectory=/home/bowen/.openclaw/workspace/telegram_forwarder
ExecStart=/home/bowen/.local/bin/uv run python forwarder.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable telegram-forwarder
sudo systemctl start telegram-forwarder
sudo systemctl status telegram-forwarder
```

## Troubleshooting

### Bot doesn't respond
- Check bot token is correct in `.env`
- Ensure bot is running (check logs)
- Verify you're using the correct owner ID

### Messages not forwarding
- Ensure bot is admin in the channel
- Check channel ID is correct (negative for channels)
- Use `/list` to see monitored channels
- Check `forwarder.log` for errors

### Permission errors
- Bot must be admin in channels to read all messages
- Some channels may require additional permissions

## Security

- Bot only responds to owner commands
- Unauthorized users are rejected
- Bot token should never be shared
- Consider adding rate limiting for production use

## License

MIT License - Feel free to modify and use as needed.
