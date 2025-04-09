import os
import re
import requests
import urllib.parse
import telebot
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from config import BOT_TOKEN, API_ID, API_HASH
from typing import Tuple, Optional

# Initialize bot and client
bot = telebot.TeleBot(BOT_TOKEN)
client = TelegramClient("xhamster_userbot", API_ID, API_HASH)

# Constants
XHAMSTER_DOMAIN = "xhamster.com"
DOWNLOAD_TIMEOUT = 60
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB (Telegram limit for bots)

class VideoDownloadError(Exception):
    pass

def extract_slug(url: str) -> Optional[str]:
    """Extract video slug from xHamster URL."""
    patterns = [
        r"xhamster\.com\/videos\/([^\/]+)",
        r"xhamster\.com\/movies\/([^\/]+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info(xh_url: str) -> Tuple[Optional[str], Optional[str]]:
    """Get video URL and thumbnail from xHamster."""
    slug = extract_slug(xh_url)
    if not slug:
        return None, None

    encoded_url = urllib.parse.quote(f"https://{XHAMSTER_DOMAIN}/videos/{slug}")
    api_url = f"https://vkrdownloader.xyz/server/?api_key=vkrdownloader&vkr={encoded_url}"

    try:
        res = requests.get(api_url, timeout=10)
        res.raise_for_status()
        data = res.json().get("data", {})
        
        thumbnail = data.get("thumbnail", "")
        downloads = data.get("downloads", [])

        # Filter and sort MP4 links by quality
        mp4_links = sorted(
            [d for d in downloads if d.get("url", "").endswith(".mp4")],
            key=lambda x: int(re.search(r"(\d+)p", x.get("format_id", "0p")).group(1)),
            reverse=True
        )

        return (mp4_links[0]["url"], thumbnail) if mp4_links else (None, None)

    except (requests.RequestException, ValueError, KeyError) as e:
        raise VideoDownloadError(f"Failed to fetch video info: {str(e)}")

def download_video(video_url: str, file_path: str) -> None:
    """Download video file with progress tracking."""
    try:
        with requests.get(video_url, stream=True, timeout=DOWNLOAD_TIMEOUT) as r:
            r.raise_for_status()
            
            file_size = int(r.headers.get('content-length', 0))
            if file_size > MAX_FILE_SIZE:
                raise VideoDownloadError("Video file is too large for Telegram")
                
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except requests.RequestException as e:
        raise VideoDownloadError(f"Download failed: {str(e)}")

async def send_video_with_telethon(chat_id: int, file_path: str) -> None:
    """Send video using Telethon client."""
    try:
        await client.start()
        await client.send_file(
            entity=chat_id,
            file=file_path,
            caption="🎥 Here's your video from xHamster",
            supports_streaming=True
        )
    except FloodWaitError as e:
        raise VideoDownloadError(f"Flood wait: Please wait {e.seconds} seconds before trying again")
    except Exception as e:
        raise VideoDownloadError(f"Failed to send video: {str(e)}")

@bot.message_handler(func=lambda message: message.text and XHAMSTER_DOMAIN in message.text)
def handle_message(message):
    """Handle incoming xHamster URLs."""
    url = message.text.strip()
    
    try:
        # Send initial response
        msg = bot.reply_to(message, "⏳ Processing your video, please wait...")
        
        # Get video info
        video_url, _ = get_video_info(url)
        if not video_url:
            raise VideoDownloadError("Could not find video URL")
        
        # Download video
        temp_file = f"temp_{message.message_id}.mp4"
        download_video(video_url, temp_file)
        
        # Check file size
        file_size = os.path.getsize(temp_file)
        if file_size > MAX_FILE_SIZE:
            raise VideoDownloadError("Video is too large (max 50MB)")
        
        # Edit message to show uploading status
        bot.edit_message_text("📤 Uploading video...", message.chat.id, msg.message_id)
        
        # Send video
        asyncio.run(send_video_with_telethon(message.chat.id, temp_file))
        
        # Clean up
        os.remove(temp_file)
        bot.delete_message(message.chat.id, msg.message_id)
        
    except VideoDownloadError as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
    except Exception as e:
        bot.reply_to(message, "❌ An unexpected error occurred. Please try again later.")
        print(f"Error processing message: {str(e)}")
    finally:
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    print("Bot is running...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Bot stopped: {str(e)}")
