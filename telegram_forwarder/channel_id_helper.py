#!/usr/bin/env python3
"""
Helper script to find Telegram channel IDs
"""
import asyncio
from telegram import Bot
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

async def get_updates():
    """Get recent updates to find channel IDs"""
    if not BOT_TOKEN or BOT_TOKEN == 'your_bot_token_here':
        print("❌ BOT_TOKEN not set in .env file!")
        print("Please get your token from @BotFather and add it to .env")
        return
    
    bot = Bot(token=BOT_TOKEN)
    
    print("🔍 Listening for messages...")
    print("Post a message in your channel OR send a message to your bot")
    print("Press Ctrl+C to stop\n")
    
    offset = 0
    try:
        while True:
            updates = await bot.get_updates(offset=offset, timeout=10)
            
            if updates:
                for update in updates:
                    offset = update.update_id + 1
                    
                    # Get chat info
                    if update.message:
                        chat = update.message.chat
                        print(f"\n📩 Message received!")
                        print(f"   Chat ID: {chat.id}")
                        print(f"   Chat Type: {chat.type}")
                        
                        if chat.title:
                            print(f"   Chat Title: {chat.title}")
                        if chat.username:
                            print(f"   Chat Username: @{chat.username}")
                        
                        if update.message.text:
                            print(f"   Message: {update.message.text[:50]}...")
                        
                        print(f"\n   ✅ Add this to CHANNELS_TO_FORWARD in .env:")
                        print(f"   {chat.id}")
                        
    except KeyboardInterrupt:
        print("\n\n✅ Stopped listening")

if __name__ == '__main__':
    asyncio.run(get_updates())
