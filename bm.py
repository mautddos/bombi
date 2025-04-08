import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# List of video URLs
VIDEOS = [
    "https://t.me/botstomp/3?single",
    "https://t.me/botstomp/3?single",
    "https://t.me/botstomp/4?single",
    "https://t.me/botstomp/5?single",
    "https://t.me/botstomp/6?single",
    "https://t.me/botstomp/7?single",
    "https://t.me/botstomp/8?single",
    "https://t.me/botstomp/9?single",
    "https://t.me/botstomp/10?single"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text("Hi! Use /sendvideos to send all the videos.")

async def send_videos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send all videos from the list one by one."""
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, f"Sending {len(VIDEOS)} videos...")
    
    for video_url in VIDEOS:
        try:
            await context.bot.send_video(chat_id=chat_id, video=video_url)
        except Exception as e:
            logger.error(f"Failed to send video {video_url}: {e}")
            await context.bot.send_message(chat_id, f"Failed to send video: {video_url}")
    
    await context.bot.send_message(chat_id, "All videos sent!")

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("8180063318:AAG2FtpVESnPYKuEszDIaewy-LXgVXXDS-o").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("sendvideos", send_videos))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
