import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import filters  # Note: lowercase 'filters' in v20+

# Video URLs array
VIDEOS = [
    "https://t.me/botstomp/21?single",
    "https://t.me/botstomp/22?single",
    "https://t.me/botstomp/23?single",
    "https://t.me/botstomp/24?single",
    "https://t.me/botstomp/25?single",
    "https://t.me/botstomp/26?single",
    "https://t.me/c/2441094491/8889",
    "https://t.me/c/2441094491/8890",
    "https://t.me/botstomp/27?single",
    "https://t.me/botstomp/28?single",
    "https://t.me/botstomp/29?single",
    "https://t.me/botstomp/30?single"
]

# Main menu keyboard
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Dasi test🍊", "Dasi mms🍊"],
        ["New Videos 1🎬", "New Videos 2🎬"],
        ["Premium Content💎", "Back to Main🔙"]
    ],
    resize_keyboard=True
)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "🌟 Welcome to the Video Bot! 🌟",
        reply_markup=MAIN_KEYBOARD
    )

def send_videos(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    for video in VIDEOS:
        context.bot.send_video(chat_id=chat_id, video=video)

def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if text in ["Dasi test🍊", "Dasi mms🍊", "New Videos 1🎬", "New Videos 2🎬", "Premium Content💎"]:
        send_videos(update, context)
    elif text == "Back to Main🔙":
        start(update, context)

def main() -> None:
    TOKEN = os.getenv('TELEGRAM_TOKEN') or '8125880528:AAHRUQpcmN645oKmvjt8OeGSGVjG_9Aas38'
    
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    updater.start_polling()
    print("✅ Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
