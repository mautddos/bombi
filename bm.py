import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Bot Configuration
BOT_TOKEN = "8125880528:AAHRUQpcmN645oKmvjt8OeGSGVjG_9Aas38"
CHANNEL_ID = -1002441094491  # Channel with videos
VERIFICATION_CHANNEL = -1002440538814  # Channel user must join

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store user progress and verification status
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with channel join button"""
    user_id = update.effective_user.id
    username = update.effective_user.full_name
    
    welcome_msg = f"""
🌟 *Welcome {username}!* 🌟

🔞 This bot provides adult content. You must be 18+ to use this bot.

✅ *Features:*
- High quality videos
- Regular updates
- Fast delivery

⚠️ *Rules:*
1. Don't spam
2. No sharing of illegal content
3. Respect other users

Click the button below to join our channel and unlock the content!
    """
    
    keyboard = [
        [InlineKeyboardButton("🔞 Join Channel", url=f"https://t.me/+LNs_qcLHlbNkN2E1")],
        [InlineKeyboardButton("✅ Verify Join", callback_data='verify_join')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Store that we've sent the initial message to this user
    user_data[user_id] = {'verified': False}
    
    await update.message.reply_text(
        welcome_msg,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if user has joined the channel"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    try:
        member = await context.bot.get_chat_member(VERIFICATION_CHANNEL, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            # User has joined the channel
            user_data[user_id]['verified'] = True
            
            # Send video menu
            keyboard = [
                [InlineKeyboardButton("🎬 Get Videos", callback_data='get_videos')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "✅ *Verification successful!*\n\nClick below to get videos:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await query.answer("❌ You haven't joined the channel yet!", show_alert=True)
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        await query.answer("❌ Verification failed. Please try again.", show_alert=True)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all button callbacks"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {'verified': False}
    
    if query.data == 'verify_join':
        await verify_join(update, context)
    elif query.data == 'get_videos':
        if user_data[user_id]['verified']:
            await send_video_batch(update, context)
        else:
            await query.answer("Please verify you've joined the channel first!", show_alert=True)
    elif query.data == 'next_batch':
        if user_data[user_id]['verified']:
            await send_video_batch(update, context)
        else:
            await query.answer("Verification expired. Please verify again.", show_alert=True)

async def send_video_batch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a batch of 20 videos from the channel"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Initialize user progress if not exists
    if 'last_sent' not in user_data[user_id]:
        user_data[user_id]['last_sent'] = 0
    
    start_msg = user_data[user_id]['last_sent']
    end_msg = start_msg + 20  # Send 20 videos at a time
    sent_count = 0
    
    # Edit original message to show loading
    await query.edit_message_text("⏳ Preparing your videos...")
    
    for msg_id in range(start_msg + 1, end_msg + 1):
        try:
            await context.bot.copy_message(
                chat_id=query.message.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to copy message {msg_id}: {e}")
    
    if sent_count > 0:
        user_data[user_id]['last_sent'] = end_msg
        
        # Add Next button
        keyboard = [
            [InlineKeyboardButton("⏭ Next Batch (20 Videos)", callback_data='next_batch')],
            [InlineKeyboardButton("🔄 Refresh Menu", callback_data='get_videos')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=f"📦 Sent {sent_count} videos\n\nClick below for more:",
            reply_markup=reply_markup
        )
    else:
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text="❌ No more videos available or failed to send.\n\nTry again later!"
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors"""
    logger.error(msg="Exception while handling update:", exc_info=context.error)

def main() -> None:
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT, start))
    
    # Error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    application.run_polling()
    logger.info("Bot is now running...")

if __name__ == '__main__':
    main()
