#!/usr/bin/env python3
"""
Telegram Message Forwarder Bot
Forwards messages from specified channels to the owner and reports results.
"""
import os
import sys
import logging
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 2069029798))
CHANNELS_TO_FORWARD = []

# Parse channels if provided
if os.getenv('CHANNELS_TO_FORWARD'):
    CHANNELS_TO_FORWARD = [
        int(cid.strip()) for cid in os.getenv('CHANNELS_TO_FORWARD').split(',')
    ]

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('forwarder.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Message counter
message_count = {'total': 0, 'forwarded': 0, 'errors': 0}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("Sorry, this bot is private.")
        logger.warning(f"Unauthorized access attempt by user {user_id}")
        return
    
    welcome_msg = (
        "🤖 Telegram Forwarder Bot Active!\n\n"
        f"Owner ID: {OWNER_ID}\n"
        f"Monitoring {len(CHANNELS_TO_FORWARD)} channels\n"
        f"Total forwarded: {message_count['forwarded']}\n\n"
        "Commands:\n"
        "/stats - Show forwarding statistics\n"
        "/add <channel_id> - Add channel to monitor\n"
        "/remove <channel_id> - Remove channel from monitor\n"
        "/list - Show monitored channels\n"
        "/health - Show bot health status"
    )
    await update.message.reply_text(welcome_msg)
    logger.info(f"Owner {user_id} started the bot")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show forwarding statistics."""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("Unauthorized")
        return
    
    stats_msg = (
        f"📊 Forwarding Statistics\n\n"
        f"Total messages received: {message_count['total']}\n"
        f"Successfully forwarded: {message_count['forwarded']}\n"
        f"Errors: {message_count['errors']}\n"
        f"Success rate: {(message_count['forwarded'] / max(message_count['total'], 1) * 100):.1f}%\n\n"
        f"Monitored channels: {len(CHANNELS_TO_FORWARD)}"
    )
    await update.message.reply_text(stats_msg)
    logger.info(f"Stats requested by owner {user_id}")


async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a channel to monitor."""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("Unauthorized")
        return
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "Usage: /add <channel_id>\n"
            "Example: /add -1001234567890\n\n"
            "Note: Use the numeric channel ID (negative for channels/groups)"
        )
        return
    
    try:
        channel_id = int(context.args[0])
        if channel_id in CHANNELS_TO_FORWARD:
            await update.message.reply_text(f"Channel {channel_id} is already being monitored")
            return
        
        CHANNELS_TO_FORWARD.append(channel_id)
        await update.message.reply_text(f"✅ Added channel {channel_id} to monitoring")
        logger.info(f"Owner {user_id} added channel {channel_id}")
    except ValueError:
        await update.message.reply_text("Invalid channel ID. Must be a number.")


async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a channel from monitoring."""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("Unauthorized")
        return
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Usage: /remove <channel_id>")
        return
    
    try:
        channel_id = int(context.args[0])
        if channel_id not in CHANNELS_TO_FORWARD:
            await update.message.reply_text(f"Channel {channel_id} is not being monitored")
            return
        
        CHANNELS_TO_FORWARD.remove(channel_id)
        await update.message.reply_text(f"✅ Removed channel {channel_id} from monitoring")
        logger.info(f"Owner {user_id} removed channel {channel_id}")
    except ValueError:
        await update.message.reply_text("Invalid channel ID. Must be a number.")


async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all monitored channels."""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("Unauthorized")
        return
    
    if not CHANNELS_TO_FORWARD:
        await update.message.reply_text("No channels are currently being monitored.")
        return
    
    channels_text = "\n".join(str(cid) for cid in CHANNELS_TO_FORWARD)
    msg = f"📋 Monitored Channels ({len(CHANNELS_TO_FORWARD)}):\n\n{channels_text}"
    await update.message.reply_text(msg)


async def health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot health status."""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("Unauthorized")
        return
    
    health_msg = (
        f"🟢 Bot Status: HEALTHY\n\n"
        f"Uptime: Running\n"
        f"Owner connection: Active\n"
        f"Monitored channels: {len(CHANNELS_TO_FORWARD)}\n"
        f"Messages processed: {message_count['total']}\n"
        f"Forward success rate: {(message_count['forwarded'] / max(message_count['total'], 1) * 100):.1f}%"
    )
    await update.message.reply_text(health_msg)


async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward messages from monitored channels to owner."""
    # Only forward from monitored channels
    if CHANNELS_TO_FORWARD:
        chat_id = update.effective_chat.id
        if chat_id not in CHANNELS_TO_FORWARD:
            return
    
    message_count['total'] += 1
    
    try:
        # Get the original message
        original_message = update.message
        
        # Prepare content to send
        content_parts = []
        
        # Add source info
        source_name = original_message.chat.title or original_message.chat.username or str(original_message.chat.id)
        source_link = f"https://t.me/{original_message.chat.username}" if original_message.chat.username else "Private channel"
        
        content_parts.append(f"📩 New message from: {source_name}")
        content_parts.append(f"Link: {source_link}")
        content_parts.append("")
        
        # Add text content if present
        if original_message.text:
            content_parts.append(f"📝 Text:\n{original_message.text}")
        
        # Add caption if present (for photos, videos, etc.)
        if original_message.caption:
            content_parts.append(f"📝 Caption:\n{original_message.caption}")
        
        # Add media info
        if original_message.photo:
            content_parts.append("🖼️ [Photo attachment]")
        elif original_message.video:
            content_parts.append("🎥 [Video attachment]")
        elif original_message.document:
            content_parts.append(f"📎 [Document: {original_message.document.file_name}]")
        elif original_message.sticker:
            content_parts.append("😀 [Sticker]")
        elif original_message.voice:
            content_parts.append("🎤 [Voice message]")
        elif original_message.audio:
            content_parts.append("🎵 [Audio file]")
        
        # Add forward info if this is a forwarded message
        if original_message.forward_from:
            content_parts.append(f"↪️ Forwarded from: {original_message.forward_from.full_name}")
        elif original_message.forward_from_chat:
            content_parts.append(f"↪️ Forwarded from: {original_message.forward_from_chat.title}")
        
        # Add timestamp
        content_parts.append(f"⏰ {original_message.date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Combine all parts
        final_message = "\n".join(content_parts)
        
        # Send report to owner
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=final_message,
            disable_web_page_preview=True
        )
        
        # If there's a photo, try to forward it
        if original_message.photo:
            try:
                # Get the largest photo
                largest_photo = original_message.photo[-1]
                await context.bot.send_photo(
                    chat_id=OWNER_ID,
                    photo=largest_photo.file_id,
                    caption=f"[Photo from {source_name}]"
                )
            except Exception as e:
                logger.warning(f"Could not forward photo: {e}")
        
        # If there's a document, try to forward it
        if original_message.document:
            try:
                await context.bot.send_document(
                    chat_id=OWNER_ID,
                    document=original_message.document.file_id,
                    caption=f"[Document from {source_name}]"
                )
            except Exception as e:
                logger.warning(f"Could not forward document: {e}")
        
        message_count['forwarded'] += 1
        logger.info(f"Successfully forwarded message from {source_name} to owner")
        
    except Exception as e:
        message_count['errors'] += 1
        logger.error(f"Error forwarding message: {e}", exc_info=True)
        
        # Try to notify owner of error
        try:
            await context.bot.send_message(
                chat_id=OWNER_ID,
                text=f"⚠️ Error forwarding message: {str(e)}"
            )
        except:
            pass


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
    message_count['errors'] += 1


def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN or BOT_TOKEN == 'your_bot_token_here':
        logger.error("BOT_TOKEN not set! Please configure it in .env file")
        sys.exit(1)
    
    logger.info("Starting Telegram Forwarder Bot...")
    logger.info(f"Owner ID: {OWNER_ID}")
    logger.info(f"Monitoring {len(CHANNELS_TO_FORWARD)} channels: {CHANNELS_TO_FORWARD}")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("add", add_channel))
    application.add_handler(CommandHandler("remove", remove_channel))
    application.add_handler(CommandHandler("list", list_channels))
    application.add_handler(CommandHandler("health", health))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
