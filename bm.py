import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import Filters  # Using v13.x syntax

# Single video URL
VIDEO_LINK = "https://t.me/c/2441094491/8889"

# Simplified keyboard
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Get Video🎬"],
        ["Help❓", "Aboutℹ️"]
    ],
    resize_keyboard=True
)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "✨ Welcome to the Video Bot! ✨\n"
        "Press 'Get Video🎬' to receive the content.",
        reply_markup=MAIN_KEYBOARD
    )

def send_video(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    try:
        context.bot.send_message(
            chat_id=chat_id,
            text=f"Here's your video:\n{VIDEO_LINK}"
        )
    except Exception as e:
        print(f"Failed to send video: {e}")

def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if text == "Get Video🎬":
        send_video(update, context)
    elif text == "Help❓":
        update.message.reply_text("Just press 'Get Video🎬' to receive the content.")
    elif text == "Aboutℹ️":
        update.message.reply_text("This bot provides exclusive video content.")

def main() -> None:
    TOKEN = os.getenv('TELEGRAM_TOKEN') or '8125880528:AAHRUQpcmN645oKmvjt8OeGSGVjG_9Aas38'
    
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    print("✅ Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
