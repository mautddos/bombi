import os
import subprocess
import tempfile
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "7554221154:AAF6slUuJGJ7tXuIDhEZP8LIOB5trSTz0gU"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to the HLS Video Downloader Bot!\n\n"
        "Send me an HLS (.m3u8) URL and I'll download and send you the video."
    )

def download_hls(url: str) -> str:
    """Download HLS stream and return path to the converted MP4 file"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = os.path.join(tmp_dir, "output.mp4")
        
        # First verify the URL is accessible
        try:
            response = requests.head(url, timeout=10)
            if response.status_code != 200:
                raise Exception("HLS URL not accessible")
        except requests.RequestException:
            raise Exception("Could not connect to HLS server")
        
        # Use ffmpeg to download and convert
        command = [
            'ffmpeg',
            '-i', url,
            '-c', 'copy',         # Copy streams without re-encoding
            '-f', 'mp4',         # Output format
            '-movflags', 'frag_keyframe+empty_moov',  # For streaming
            output_file
        ]
        
        try:
            subprocess.run(command, check=True, stderr=subprocess.PIPE, timeout=300)
            return output_file
        except subprocess.TimeoutExpired:
            raise Exception("Download timed out after 5 minutes")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown error"
            raise Exception(f"FFmpeg error: {error_msg}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()
    
    if not url.lower().endswith('.m3u8'):
        await update.message.reply_text("Please send a valid HLS (.m3u8) URL.")
        return
    
    try:
        msg = await update.message.reply_text("⏳ Downloading HLS stream... (This may take a while)")
        
        video_path = download_hls(url)
        
        # Send video with progress updates
        await msg.edit_text("✅ Download complete! Sending video...")
        with open(video_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="Here's your downloaded video!",
                supports_streaming=True,
                width=1280,
                height=720,
                duration=60  # Approximate duration
            )
        await msg.delete()
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        print(f"Error: {str(e)}")

def main() -> None:
    # Check if ffmpeg is installed
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        print("CRITICAL ERROR: ffmpeg is not installed. Please install it first.")
        print("On Ubuntu/Debian: sudo apt install ffmpeg")
        print("On CentOS/RHEL: sudo yum install ffmpeg")
        print("On macOS: brew install ffmpeg")
        return

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
