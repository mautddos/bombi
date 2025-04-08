import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "8180063318:AAG2FtpVESnPYKuEszDIaewy-LXgVXXDS-o"
CHANNEL_ID = -1002441094491  # Private channel ID (with -100 prefix)
ADMIN_USER_IDS = [8167507955]  # Your user ID(s) who can control the bot

async def is_admin(update: Update) -> bool:
    """Check if user is admin."""
    return update.effective_user.id in ADMIN_USER_IDS

async def post_init(application: Application) -> None:
    """Post initialization - set bot commands."""
    await application.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("menu", "Show video menu")
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message."""
    if not await is_admin(update):
        await update.message.reply_text("⚠️ You are not authorized to use this bot.")
        return
    
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main menu with video options."""
    keyboard = [
        [
            InlineKeyboardButton("Dasi video 1", callback_data="video_1"),
            InlineKeyboardButton("Dasi video 2", callback_data="video_2"),
            InlineKeyboardButton("Dasi video 3", callback_data="video_3")
        ],
        [
            InlineKeyboardButton("Dasi video 4", callback_data="video_4"),
            InlineKeyboardButton("Dasi video 5", callback_data="video_5"),
            InlineKeyboardButton("Dasi video 6", callback_data="video_6")
        ],
        [
            InlineKeyboardButton("Dasi video 7", callback_data="video_7"),
            InlineKeyboardButton("Dasi video 8", callback_data="video_8"),
            InlineKeyboardButton("Dasi video 9", callback_data="video_9")
        ],
        [
            InlineKeyboardButton("Dasi video 10", callback_data="video_10"),
            InlineKeyboardButton("Back to Main", callback_data="main_menu")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text="*ㅤ*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text="*ㅤ*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    if not await is_admin(update):
        await query.edit_message_text("⚠️ You are not authorized to use this bot.")
        return
    
    if query.data == "main_menu":
        await show_main_menu(update, context)
    elif query.data.startswith("video_"):
        video_num = query.data.split("_")[1]
        msg_id = {
            "1": 8915,
            "2": 8916,
            "3": 8917,
            "4": 8918,
            "5": 8919,
            "6": 8920,
            "7": 8921,
            "8": 8922,
            "9": 8923,
            "10": 8924
        }.get(video_num, 8915)  # Default to first video if not found
        
        try:
            await context.bot.copy_message(
                chat_id=query.message.chat_id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id
            )
        except Exception as e:
            logger.error(f"Failed to send video {msg_id}: {e}")
            await query.message.reply_text(f"❌ Failed to send video {video_num}")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", show_main_menu))
    
    # Button handler
    application.add_handler(CallbackQueryHandler(handle_button))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
