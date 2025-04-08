import os
import requests
import subprocess
import tempfile
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import filters  # Changed from Filters to filters

# Replace with your bot token
TOKEN = "7554221154:AAF6slUuJGJ7tXuIDhEZP8LIOB5trSTz0gU"

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Welcome to the HLS Downloader Bot!\n\n"
        "Send me an HLS (.m3u8) URL and I'll download and send you the video.\n\n"
        "Example URL: https://example.com/video.m3u8"
    )

def download_hls(url: str) -> str:
    """Download HLS stream and return path to the converted MP4 file"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = os.path.join(tmp_dir, "output.mp4")
        
        # Use ffmpeg to download and convert the HLS stream
        command = [
            'ffmpeg',
            '-i', url,
            '-c', 'copy',
            '-f', 'mp4',
            output_file
        ]
        
        try:
            subprocess.run(command, check=True, stderr=subprocess.PIPE)
            return output_file
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e.stderr.decode()}")
            raise Exception("Failed to download and convert the HLS stream")

def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text.strip()
    
    if not url.lower().endswith('.m3u8'):
        update.message.reply_text("Please send a valid HLS (.m3u8) URL.")
        return
    
    try:
        update.message.reply_text("⏳ Downloading and processing the video...")
        
        # Download and convert the HLS stream
        video_path = download_hls(url)
        
        # Send the video back to the user
        with open(video_path, 'rb') as video_file:
            update.message.reply_video(
                video=video_file,
                caption="Here's your downloaded video!",
                supports_streaming=True
            )
            
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")
        print(f"Error processing {url}: {str(e)}")

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Updated filters usage

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
