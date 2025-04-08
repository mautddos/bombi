import os
import subprocess
import tempfile
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "7554221154:AAF6slUuJGJ7tXuIDhEZP8LIOB5trSTz0gU"

# Custom headers to mimic a browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://example.com',
    'Referer': 'https://example.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🚀 Advanced HLS Downloader Bot\n\n"
        "Send me an HLS (.m3u8) URL and I'll process it for you\n\n"
        "Note: Large videos may take several minutes"
    )

def verify_hls_url(url: str) -> bool:
    """Check if HLS URL is accessible with custom headers"""
    try:
        response = requests.head(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return True
        
        # Try with GET if HEAD fails
        response = requests.get(url, headers=HEADERS, timeout=10)
        return response.status_code == 200
        
    except requests.RequestException:
        return False

def download_hls(url: str) -> str:
    """Download protected HLS stream with headers"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = os.path.join(tmp_dir, "output.mp4")
        
        # FFmpeg command with headers
        command = [
            'ffmpeg',
            '-headers', '\r\n'.join(f'{k}: {v}' for k, v in HEADERS.items()),
            '-i', url,
            '-c', 'copy',
            '-f', 'mp4',
            '-movflags', 'frag_keyframe+empty_moov',
            output_file
        ]
        
        try:
            subprocess.run(command, check=True, stderr=subprocess.PIPE, timeout=600)
            return output_file
        except subprocess.TimeoutExpired:
            raise Exception("Server took too long to respond (10 minute timeout)")
        except subprocess.CalledProcessError as e:
            error = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
            if "403 Forbidden" in error:
                raise Exception("Server blocked our request (403 Forbidden)")
            elif "404 Not Found" in error:
                raise Exception("Video not found (404)")
            else:
                raise Exception(f"Download failed: {error[:200]}...")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()
    
    if not url.lower().endswith(('.m3u8', '.mp4')):
        await update.message.reply_text("🔍 Please send a valid HLS (.m3u8) or MP4 URL")
        return
    
    try:
        # Check URL first
        status_msg = await update.message.reply_text("🔍 Checking URL accessibility...")
        
        if not verify_hls_url(url):
            await status_msg.edit_text("❌ URL is not accessible. It may be:\n"
                                     "- Expired\n- Geo-blocked\n- Require special headers\n"
                                     "- Private/restricted content")
            return
            
        await status_msg.edit_text("⏳ Downloading stream (may take 5-10 minutes for long videos)...")
        
        video_path = download_hls(url)
        
        # Get video duration for Telegram
        duration = 0
        try:
            probe = subprocess.run([
                'ffprobe', '-v', 'error', '-show_entries', 
                'format=duration', '-of', 
                'default=noprint_wrappers=1:nokey=1', video_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            duration = int(float(probe.stdout.strip()))
        except:
            pass
            
        await status_msg.edit_text("📤 Uploading to Telegram...")
        with open(video_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="✅ Download complete!",
                supports_streaming=True,
                duration=duration,
                width=1280,
                height=720
            )
        await status_msg.delete()
        
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")
        if 'status_msg' in locals():
            await status_msg.delete()

def main():
    # Verify ffmpeg installation
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, 
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        print("Error: ffmpeg is not installed. Please install it first:")
        print("Ubuntu/Debian: sudo apt install ffmpeg")
        print("CentOS/RHEL: sudo yum install ffmpeg")
        print("macOS: brew install ffmpeg")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
