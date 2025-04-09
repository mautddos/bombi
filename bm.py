import logging
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import subprocess
import tempfile

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token (consider using environment variables for security)
TOKEN = "7822455054:AAF-C_XdQBIAAWEXYDqQ2lrsIf1ewmDa46s"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! I am SEMXI VIDEO DOWNLOADER. Send me any message and I will process and send you the video.')

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process and send the video when user sends any message."""
    try:
        # Inform user we're processing
        await update.message.reply_text("Processing your video, please wait...")
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            hls_url = "https://video-cf.xhcdn.com/8yE%2BseHYuE%2B6V0skGFlDrvM8w2V1Xg3Wy4L98rG6%2Bs0%3D/56/1744113600/media=hls4/multi=256x144:144p,426x240:240p/017/235/029/240p.h264.mp4.m3u8"
            output_file = os.path.join(tmp_dir, "output.mp4")
            
            # Download and convert using ffmpeg
            command = [
                'ffmpeg',
                '-i', hls_url,
                '-c', 'copy',
                '-f', 'mp4',
                output_file
            ]
            
            # Run ffmpeg command
            subprocess.run(command, check=True)
            
            # Send the converted video
            with open(output_file, 'rb') as video_file:
                await update.message.reply_video(video=video_file)
                
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e}")
        await update.message.reply_text("Error processing video stream. Please try again later.")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Sorry, I couldn't process and send the video. Please try again later.")

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
