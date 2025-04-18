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
    if not update.message:
        return
        
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
        [InlineKeyboardButton("🔞 Join Channel", url="https://t.me/c/2440538814")],  # Updated URL format
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
        # First check if user is in user_data
        if user_id not in user_data:
            user_data[user_id] = {'verified': False}
            
        # Check channel membership
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
            await query.answer("❌ Please make sure you've joined the channel and try again.", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error in verify_join: {e}")
        await query.answer("❌ An error occurred. Please try again.", show_alert=True)

# ... [rest of your code remains the same]
