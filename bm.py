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

# Configuration - Use environment variables for sensitive data
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8125880528:AAHRUQpcmN645oKmvjt8OeGSGVjG_9Aas38')
CHANNEL_ID = -1002441094491  # Channel where videos are stored
VERIFICATION_CHANNEL_ID = -1002363906868  # Channel users must join
CHANNEL_USERNAME = "seedhe_maut"  # Without @ symbol
ADMIN_IDS = {8167507955}  # Add more admin IDs as needed

# Store user progress and bot data
user_progress = defaultdict(dict)
bot_start_time = datetime.now()
total_users = 0

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Blocklist functionality
blocked_users = set()

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
    
    await update.message.reply_text(
        text=welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

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
    end_msg = start_msg + 10
    sent_count = 0
    
    for msg_id in range(start_msg + 1, end_msg + 1):
        try:
            await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id,
                disable_notification=True
            )
            sent_count += 1
            await asyncio.sleep(0.5)  # Rate limiting
        except Exception as e:
            logger.error(f"Failed to copy message {msg_id}: {e}")
    
    if sent_count > 0:
        user_progress[user_id]['last_sent'] = end_msg
        keyboard = [[InlineKeyboardButton("Next", callback_data='next')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(
            chat_id=chat_id,
            text=f"Sent {sent_count} videos.",
            reply_markup=reply_markup
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text="No more videos available or failed to send."
        )

# Admin commands
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    uptime = datetime.now() - bot_start_time
    days, seconds = uptime.days, uptime.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    status_text = (
        f"🤖 <b>Bot Status</b>\n\n"
        f"⏳ <b>Uptime:</b> {days}d {hours}h {minutes}m {seconds}s\n"
        f"👥 <b>Total Users:</b> {total_users}\n"
        f"📊 <b>Active Users:</b> {len(user_progress)}\n"
        f"🚫 <b>Blocked Users:</b> {len(blocked_users)}\n"
        f"📅 <b>Last Start:</b> {bot_start_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await update.message.reply_text(status_text, parse_mode='HTML')

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /block <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        blocked_users.add(user_id)
        await update.message.reply_text(f"✅ User {user_id} has been blocked.")
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a numeric ID.")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /unblock <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        if user_id in blocked_users:
            blocked_users.remove(user_id)
            await update.message.reply_text(f"✅ User {user_id} has been unblocked.")
        else:
            await update.message.reply_text(f"User {user_id} is not blocked.")
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please provide a numeric ID.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = ' '.join(context.args)
    success = 0
    failed = 0
    
    for user_id in user_progress:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            success += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            failed += 1
    
    await update.message.reply_text(
        f"📢 Broadcast completed:\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}"
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update and hasattr(update, 'effective_user'):
        user_id = update.effective_user.id
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="Sorry, an error occurred. Please try again later."
            )
        except Exception:
            pass

def main() -> None:
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
