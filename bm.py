import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token from BotFather
TOKEN = "7822455054:AAF-C_XdQBIAAWEXYDqQ2lrsIf1ewmDa46s"

# The video URL you provided
VIDEO_URL = "https://video-cf.xhcdn.com/8yE%2BseHYuE%2B6V0skGFlDrvM8w2V1Xg3Wy4L98rG6%2Bs0%3D/56/1744113600/media=hls4/multi=256x144:144p,426x240:240p/017/235/029/240p.h264.mp4.m3u8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! Send me any message and I will send you the video.')

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the video when user sends any message."""
    try:
        await update.message.reply_video(VIDEO_URL)
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
