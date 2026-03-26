#!/bin/bash
# Setup script for Telegram Forwarder Bot

set -e

echo "🤖 Telegram Forwarder Bot Setup"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your:"
    echo "   - BOT_TOKEN (from @BotFather)"
    echo "   - OWNER_ID (your Telegram user ID: 2069029798)"
    echo "   - CHANNELS_TO_FORWARD (comma-separated channel IDs)"
    echo ""
    echo "Press Enter to open .env in nano editor..."
    read
    nano .env
else
    echo "✅ .env file already exists"
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
if command -v uv &> /dev/null; then
    uv pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

echo "✅ Dependencies installed"
echo ""

# Make forwarder.py executable
chmod +x forwarder.py

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Ensure your .env is configured correctly"
echo "2. Run: uv run python forwarder.py"
echo "3. Send /start to the bot in Telegram"
echo ""
echo "For more info, see README.md"
