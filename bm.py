import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8125880528:AAHRUQpcmN645oKmvjt8OeGSGVjG_9Aas38')
CHANNEL_ID = -1002441094491  # Channel where videos are stored
VERIFICATION_CHANNEL_ID = -1002363906868  # Channel users must join
CHANNEL_USERNAME = "seedhe_maut"  # Without @ symbol
ADMIN_IDS = {8167507955}  # Admin user IDs
DELETE_AFTER_SECONDS = 120  # Auto-delete messages after 2 minutes

# Store user progress and bot data
user_progress = defaultdict(dict)
bot_start_time = datetime.now()
total_users = 0
blocked_users = set()
sent_messages = defaultdict(list)  # {user_id: [(chat_id, message_id, is_media), ...]}

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global application reference for cleanup tasks
application = None

async def delete_message_after_delay(chat_id: int, message_id: int, delay: int, is_media: bool):
    """Delete a message after specified delay if it's a media message"""
    await asyncio.sleep(delay)
    try:
        if is_media:  # Only delete if it's a media message
            await application.bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.info(f"Deleted media message {message_id} in chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to delete message {message_id}: {e}")

async def cleanup_user_messages(user_id: int):
    """Cleanup all scheduled messages for a user"""
    if user_id in sent_messages:
        for chat_id, message_id, is_media in sent_messages[user_id]:
            if is_media:  # Only try to delete media messages
                try:
                    await application.bot.delete_message(chat_id=chat_id, message_id=message_id)
                except Exception as e:
                    logger.error(f"Failed to delete message {message_id} for user {user_id}: {e}")
        del sent_messages[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id in blocked_users:
        await update.message.reply_text("🚫 You are blocked from using this bot.")
        return
    
    global total_users
    total_users += 1
    
    # Notify admin about new user
    await notify_admin(context.bot, f"👤 New user:\nID: {user.id}\nUsername: @{user.username}\nName: {user.full_name}")
    
    welcome_text = """
🎬 <b>Welcome to Video Bot!</b> 🎬

Here you can get access to our exclusive video collection.

Please join our channel first to use this bot:
@seedhe_maut
"""
    keyboard = [
        [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton("✅ I've Joined", callback_data='check_join')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    sent_message = await update.message.reply_text(
        text=welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    # Don't schedule deletion for this text message

async def notify_admin(bot, message: str):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=message)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in blocked_users:
        await query.edit_message_text(text="🚫 You are blocked from using this bot.")
        return

    if query.data == 'check_join':
        try:
            chat_member = await context.bot.get_chat_member(VERIFICATION_CHANNEL_ID, user_id)
            if chat_member.status in ['member', 'administrator', 'creator']:
                keyboard = [[InlineKeyboardButton("Get Videos", callback_data='videos')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    text="Thanks for joining! Click below to get videos:",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(text="Please join the channel first to access videos.")
        except Exception as e:
            logger.error(f"Error checking membership: {e}")
            await query.edit_message_text(text="Couldn't verify your channel membership. Please try again.")
    
    elif query.data == 'videos':
        user_progress[user_id]['last_sent'] = 0
        await send_batch(context.bot, user_id, query.message.chat.id)
    
    elif query.data == 'next':
        await send_batch(context.bot, user_id, query.message.chat.id)

async def send_batch(bot, user_id, chat_id):
    if user_id not in user_progress or 'last_sent' not in user_progress[user_id]:
        user_progress[user_id]['last_sent'] = 0
    
    start_msg = user_progress[user_id]['last_sent']
    end_msg = start_msg + 100
    sent_count = 0
    
    for msg_id in range(start_msg + 1, end_msg + 1):
        try:
            # First get the message to check its type
            channel_message = await bot.get_chat_message(chat_id=CHANNEL_ID, message_id=msg_id)
            
            # Check if the message contains video or photo
            is_media = bool(channel_message.video or channel_message.photo)
            
            sent_message = await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id,
                disable_notification=True
            )
            sent_count += 1
            
            # Schedule deletion only for media messages
            if is_media:
                asyncio.create_task(delete_message_after_delay(chat_id, sent_message.message_id, DELETE_AFTER_SECONDS, is_media))
                sent_messages[user_id].append((chat_id, sent_message.message_id, is_media))
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Failed to copy message {msg_id}: {e}")
    
    if sent_count > 0:
        user_progress[user_id]['last_sent'] = end_msg
        keyboard = [[InlineKeyboardButton("Next", callback_data='next')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        control_message = await bot.send_message(
            chat_id=chat_id,
            text=f"Sent {sent_count} videos (media will auto-delete in {DELETE_AFTER_SECONDS//60} mins).",
            reply_markup=reply_markup
        )
        # Don't schedule deletion for this control message
        sent_messages[user_id].append((chat_id, control_message.message_id, False))
    else:
        error_message = await bot.send_message(
            chat_id=chat_id,
            text="No more videos available or failed to send."
        )
        # Don't schedule deletion for this error message
        sent_messages[user_id].append((chat_id, error_message.message_id, False))

# [Rest of the code remains the same...]

def main() -> None:
    global application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # User commands
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    
    # Admin commands
    application.add_handler(CommandHandler('status', status))
    application.add_handler(CommandHandler('block', block_user))
    application.add_handler(CommandHandler('unblock', unblock_user))
    application.add_handler(CommandHandler('broadcast', broadcast))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
