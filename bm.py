import logging
from telegram import Update, Sticker, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from BotFather
TOKEN = "8125880528:AAEslZC6Bcgo79TisxS8v5cnuPElvbFG0FA"

# Sticker pack details
STICKER_PACK_NAME = "celebsex"
STICKER_COUNT = 10  # Update this with the actual number of stickers in the pack

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send all stickers from the specified pack when /start is received."""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    # Send a message first
    await update.message.reply_text(
        f"Hi {user.first_name}! Sending stickers from the pack...",
    )
    
    # Send all stickers from the pack
    for i in range(1, STICKER_COUNT + 1):
        sticker_id = f"CAACAgIAAxkBAAEL{STICKER_PACK_NAME}{i:02d}"  # This is a simplified format
        try:
            await update.message.reply_sticker(sticker=sticker_id)
            await asyncio.sleep(0.5)  # Small delay to avoid rate limiting
        except Exception as e:
            logger.error(f"Error sending sticker {i}: {e}")
            continue

async def post_init(application: Application) -> None:
    """Post initialization - set bot commands."""
    await application.bot.set_my_commands([
        BotCommand("start", "Get all stickers from the pack"),
    ])

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
