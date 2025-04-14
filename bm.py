import logging
from telegram import Update, BotCommand
from telegram.ext import Updater, CommandHandler, CallbackContext
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

def start(update: Update, context: CallbackContext) -> None:
    """Send all stickers from the specified pack when /start is received."""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    # Send a message first
    update.message.reply_text(
        f"Hi {user.first_name}! Sending stickers from the pack...",
    )
    
    # Send all stickers from the pack
    for i in range(1, STICKER_COUNT + 1):
        sticker_id = f"CAACAgIAAxkBAAEL{STICKER_PACK_NAME}{i:02d}"  # This is a simplified format
        try:
            update.message.reply_sticker(sticker=sticker_id)
        except Exception as e:
            logger.error(f"Error sending sticker {i}: {e}")
            continue

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == "__main__":
    main()
