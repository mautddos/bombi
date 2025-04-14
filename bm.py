import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters

# Channel & video info
CHANNEL_ID = "-1002441094491"  # Channel ID
MESSAGE_ID = 8889              # The message ID of the video

# Custom keyboard
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
    try:
        # Get original video message from channel
        original_msg = context.bot.get_chat(CHANNEL_ID).get_message(MESSAGE_ID)
        
        # Send as fresh upload (no forward tag)
        context.bot.send_video(
            chat_id=update.message.chat_id,
            video=original_msg.video.file_id,
            caption="Here’s your video 🎬",
            supports_streaming=True
        )

    except Exception as e:
        print(f"Error sending video: {e}")
        update.message.reply_text("Couldn't send video. Make sure bot is admin in the channel and video is accessible.")

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
