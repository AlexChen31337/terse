#!/usr/bin/env python3
"""
Setup script for AlphaStrike notifications
"""

import os
import sys

def setup_notifications():
    """Configure Telegram notifications for AlphaStrike"""

    print("=" * 60)
    print("AlphaStrike Notification Setup")
    print("=" * 60)
    print()

    # Get Telegram Chat ID
    print("To enable trade notifications, we need your Telegram Chat ID.")
    print()
    print("How to find your Chat ID:")
    print("1. Message @userinfobot on Telegram")
    print("2. It will reply with your Chat ID")
    print("3. Copy that number and paste below")
    print()

    chat_id = input("Enter your Telegram Chat ID (or press Enter to skip): ").strip()

    if not chat_id:
        print()
        print("⚠️  Notifications disabled. You can enable them later by:")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'")
        return

    # Save to environment file
    env_file = os.path.join(os.path.dirname(__file__), '.env')

    with open(env_file, 'w') as f:
        f.write(f"TELEGRAM_CHAT_ID={chat_id}\n")

    print()
    print(f"✅ Chat ID saved to {env_file}")
    print()
    print("🔔 Notifications enabled!")
    print("   You'll receive alerts for:")
    print("   • Every trade opened (with full analysis)")
    print("   • Every trade closed (with P&L)")
    print("   • Daily summary reports")
    print()

    # Test notification
    test = input("Send a test notification? (y/n): ").strip().lower()
    if test == 'y':
        import subprocess
        result = subprocess.run(
            ['clawdbot', 'message', 'send',
             '--channel', 'telegram',
             '--target', chat_id,
             '--message', '✅ AlphaStrike notifications configured!\n\nYou will receive alerts for all trades.'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ Test notification sent!")
        else:
            print(f"❌ Test failed: {result.stderr}")

if __name__ == "__main__":
    setup_notifications()
