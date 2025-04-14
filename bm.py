import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Video URLs array
VIDEOS = [
    "https://t.me/botstomp/21?single",
    "https://t.me/botstomp/22?single",
    "https://t.me/botstomp/23?single",
    "https://t.me/botstomp/24?single",
    "https://t.me/botstomp/25?single",
    "https://t.me/botstomp/26?single",
    "https://t.me/botstomp/27?single",
    "https://t.me/botstomp/28?single",
    "https://t.me/botstomp/29?single",
    "https://t.me/botstomp/30?single"
]

# Main menu keyboard
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Dasi test🍊", "Dasi mms🍊"],
        ["back to main"]
    ],
    resize_keyboard=True
)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "* tharki bot *",
        parse_mode='Markdown',
        reply_markup=MAIN_KEYBOARD
    )

def send_videos(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    for video in VIDEOS:
        context.bot.send_video(chat_id=chat_id, video=video)

def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if text in ["Dasi test🍊", "Dasi mms🍊"]:
        send_videos(update, context)
    elif text == "back to main":
        start(update, context)

def main() -> None:
    # Get the token from environment variable or replace with your token
    TOKEN = os.getenv('8125880528:AAHRUQpcmN645oKmvjt8OeGSGVjG_9Aas38')
    
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
