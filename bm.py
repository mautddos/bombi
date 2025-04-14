import logging
import pytz  # Import pytz for timezone support
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram video link
VIDEO_LINK = "https://t.me/botstomp/123"
BOT_TOKEN = "8125880528:AAEslZC6Bcgo79TisxS8v5cnuPElvbFG0FA"  # Replace with your actual token

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an attractive start message with buttons when the command /start is issued."""
    user = update.effective_user
    welcome_text = f"""
✨ *Welcome {user.first_name}!* ✨

🚀 *Ready to explore amazing features?* 🚀

🔹 *SU* - Super Utility
🔹 *PU* - Premium Utility
🔹 *CU* - Common Utility

Tap a button below to get started!
"""
    
    keyboard = [
        [
            InlineKeyboardButton("SU", callback_data="su"),
            InlineKeyboardButton("PU", callback_data="pu"),
        ],
        [
            InlineKeyboardButton("CU", callback_data="cu"),
            InlineKeyboardButton("Back", callback_data="back"),
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    # Define responses for each button
    responses = {
        "su": "🎉 *Super Utility* selected!\nHere's your video:",
        "pu": "💎 *Premium Utility* selected!\nHere's your video:",
        "cu": "🛠 *Common Utility* selected!\nHere's your video:",
        "back": "🔙 Returning to main menu..."
    }
    
    # Get the response text
    response_text = responses.get(query.data, "Invalid option")
    
    if query.data == "back":
        # Recreate the main menu
        keyboard = [
            [
                InlineKeyboardButton("SU", callback_data="su"),
                InlineKeyboardButton("PU", callback_data="pu"),
            ],
            [
                InlineKeyboardButton("CU", callback_data="cu"),
                InlineKeyboardButton("Back", callback_data="back"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=response_text, 
            reply_markup=reply_markup, 
            parse_mode="Markdown"
        )
    else:
        # For SU, PU, CU buttons - send the video
        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=VIDEO_LINK,
            caption=response_text,
            parse_mode="Markdown"
        )
        
        # Show the buttons again
        keyboard = [
            [
                InlineKeyboardButton("SU", callback_data="su"),
                InlineKeyboardButton("PU", callback_data="pu"),
            ],
            [
                InlineKeyboardButton("CU", callback_data="cu"),
                InlineKeyboardButton("Back", callback_data="back"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "What would you like to do next?",
            reply_markup=reply_markup
        )

def main() -> None:
    """Run the bot."""
    # Create the Application with explicit timezone
    application = Application.builder() \
        .token(BOT_TOKEN) \
        .build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    
    # Add button handler
    application.add_handler(CallbackQueryHandler(button))

    # Run the bot until the user presses Ctrl-C
    application.
