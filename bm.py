import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token (I see you shared it in your message)
TOKEN = "7822455054:AAF-C_XdQBIAAWEXYDqQ2lrsIf1ewmDa46s"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! I am SEMXI VIDEO DOWNLOADER. Send me any message and I will send you the video.')

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the video when user sends any message."""
    try:
        # Try with a direct video URL first (you'll need to replace this)
        video_url = "https://example.com/direct-video.mp4"  # Replace with actual direct video URL
        await update.message.reply_video(video_url)
        
        # Alternative: Send as document if video doesn't work
        # await update.message.reply_document(video_url)
        
    except Exception as e:
        logger.error(f"Error sending video: {e}")
        await update.message.reply_text("Sorry, I couldn't send the video. Please try again later.")

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command messages - send the video
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_video))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
