import logging
from telegram import Update, Sticker, StickerSet
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token from BotFather
TOKEN = "7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI"

# Sticker pack name (the part after addstickers/)
STICKER_PACK = "NilaaXXX"

# Dictionary to store sticker sets and current positions for each chat
sticker_data = {}

async def start(update: Update, context: CallbackContext) -> None:
    """Send a message with a button that sends stickers when pressed."""
    chat_id = update.effective_chat.id
    
    # Initialize sticker data for this chat if not exists
    if chat_id not in sticker_data:
        sticker_data[chat_id] = {
            'stickers': [],
            'current_index': 0,
            'sticker_set_loaded': False
        }
    
    # Create a button that will trigger the sticker sending
    await update.message.reply_text(
        "Click the button below to start receiving stickers!",
        reply_markup={
            "inline_keyboard": [[
                {"text": "Send Sticker", "callback_data": "send_sticker"}
            ]]
        }
    )

async def button_callback(update: Update, context: CallbackContext) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    chat_id = query.message.chat_id
    
    # Initialize if not exists
    if chat_id not in sticker_data:
        sticker_data[chat_id] = {
            'stickers': [],
            'current_index': 0,
            'sticker_set_loaded': False
        }
    
    data = sticker_data[chat_id]
    
    # Load sticker set if not already loaded
    if not data['sticker_set_loaded']:
        try:
            sticker_set = await context.bot.get_sticker_set(STICKER_PACK)
            data['stickers'] = sticker_set.stickers
            data['sticker_set_loaded'] = True
            data['current_index'] = 0
            await query.answer("Sticker pack loaded!")
        except Exception as e:
            await query.answer(f"Error loading sticker pack: {e}")
            return
    
    # Send the current sticker
    if data['stickers']:
        current_sticker = data['stickers'][data['current_index']]
        await context.bot.send_sticker(chat_id=chat_id, sticker=current_sticker.file_id)
        
        # Update index for next sticker (wrap around if at end)
        data['current_index'] = (data['current_index'] + 1) % len(data['stickers'])
        
        await query.answer()
    else:
        await query.answer("No stickers available in the pack.")

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command and callback handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_callback, pattern="^send_sticker$"))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
