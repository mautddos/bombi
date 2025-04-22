import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = '7414054511:AAG7IK7fyQfiApzxnF3rP7ZHJoWi_elWd3I'
STICKER_PACK_NAME = 'sexxxxpornnsfwlove'

def start(update: Update, context: CallbackContext) -> None:
    try:
        user = update.effective_user
        update.message.reply_text(f"Hello {user.first_name}! Fetching stickers...")
        
        sticker_set = context.bot.get_sticker_set(STICKER_PACK_NAME)
        
        for sticker in sticker_set.stickers:
            update.message.reply_sticker(sticker.file_id)
            
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("Failed to fetch stickers. Try again later.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
