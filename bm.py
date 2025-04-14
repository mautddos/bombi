import logging
import pytz  # Required for timezone support
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration - REPLACE WITH NEW TOKEN AFTER TESTING!
BOT_TOKEN = "8125880528:AAEslZC6Bcgo79TisxS8v5cnuPElvbFG0FA"  
VIDEO_LINK = "https://t.me/botstomp/123"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with buttons"""
    user = update.effective_user
    welcome_msg = f"""
🌟 *Welcome {user.first_name}!* 🌟

Choose an option below:

🔹 *SU* - Super Utility
🔹 *PU* - Premium Utility
🔹 *CU* - Common Utility
"""

    buttons = [
        [InlineKeyboardButton("SU", callback_data="su"),
         InlineKeyboardButton("PU", callback_data="pu")],
        [InlineKeyboardButton("CU", callback_data="cu"),
         InlineKeyboardButton("Back", callback_data="back")]
    ]
    
    await update.message.reply_text(
        welcome_msg,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    button_responses = {
        "su": "🎉 Super Utility video:",
        "pu": "💎 Premium Utility video:",
        "cu": "🛠 Common Utility video:",
        "back": "🔙 Returning to main menu..."
    }
    
    response = button_responses.get(query.data)
    
    if query.data == "back":
        await start(update, context)
    else:
        # Send video
        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=VIDEO_LINK,
            caption=response,
            parse_mode="Markdown"
        )
        
        # Show buttons again
        buttons = [
            [InlineKeyboardButton("SU", callback_data="su"),
             InlineKeyboardButton("PU", callback_data="pu")],
            [InlineKeyboardButton("CU", callback_data="cu"),
             InlineKeyboardButton("Back", callback_data="back")]
        ]
        await query.message.reply_text(
            "Choose another option:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

def main() -> None:
    """Start the bot"""
    try:
        # Create Application with explicit timezone
        app = Application.builder() \
            .token(BOT_TOKEN) \
            .arbitrary_callback_data(True) \
            .build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(handle_buttons))
        
        logger.info("Starting bot...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Bot failed: {e}")

if __name__ == "__main__":
    # Install required packages first:
    # pip install python-telegram-bot pytz
    main()
