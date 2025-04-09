import os
import re
import requests
import urllib.parse
import telebot
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import InputWebDocument
from typing import List, Tuple, Optional

# Configuration
BOT_TOKEN = "8145114551:AAGOU9-3ZmRVxU91cPThM8vd932rNroR3WA"
API_ID = 22625636
API_HASH = "f71778a6e1e102f33ccc4aee3b5cc697"
MAX_WORKERS = 5  # Number of concurrent downloads
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB (Telegram file size limit)

bot = telebot.TeleBot(BOT_TOKEN)
client = TelegramClient(StringSession(), API_ID, API_HASH)
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Initialize clients
async def start_clients():
    await client.start()
    print("✅ Telethon client connected successfully!")

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(start_clients())

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

def get_video_info(url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Get video URL, thumbnail, and title from xHamster."""
    slug = extract_slug(url)
    if not slug:
        return None, None, None

    encoded_url = urllib.parse.quote(f"https://xhamster.com/videos/{slug}")
    api_url = f"https://vkrdownloader.xyz/server/?api_key=vkrdownloader&vkr={encoded_url}"

    try:
        res = requests.get(api_url, timeout=10)
        data = res.json().get("data", {})
        thumbnail = data.get("thumbnail", "")
        title = data.get("title", "xHamster Video")
        downloads = data.get("downloads", [])

        # Filter and sort MP4 links by quality (highest first)
        mp4_links = sorted(
            [d for d in downloads if d.get("url", "").endswith(".mp4")],
            key=lambda x: int(re.search(r"(\d+)p", x.get("format_id", "0p")).group(1)),
            reverse=True
        )

        return (mp4_links[0]["url"], thumbnail, title) if mp4_links else (None, None, None)

    except Exception as e:
        print(f"API Error for {url}: {e}")
        return None, None, None

def download_file(url: str, file_path: str) -> bool:
    """Download file with progress tracking."""
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            if total_size > MAX_FILE_SIZE:
                print(f"File too large: {total_size} bytes")
                return False
                
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        print(f"Download failed for {url}: {e}")
        return False

async def send_video(chat_id: int, file_path: str, thumb_url: str, caption: str):
    """Send video with thumbnail using Telethon."""
    try:
        # Download thumbnail if available
        thumb_path = None
        if thumb_url:
            thumb_path = f"thumb_{chat_id}.jpg"
            if not download_file(thumb_url, thumb_path):
                thumb_path = None

        await client.send_file(
            entity=chat_id,
            file=file_path,
            thumb=thumb_path,
            caption=caption,
            supports_streaming=True,
            attributes=None,
            progress_callback=lambda c, t: print(f"Uploaded {c} of {t} bytes")
        )
        
        # Clean up
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
            
    except Exception as e:
        print(f"Error sending video to {chat_id}: {e}")
        raise
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def process_single_url(url: str, chat_id: int):
    """Process a single xHamster URL."""
    try:
        bot.send_chat_action(chat_id, 'typing')
        video_url, thumb_url, title = get_video_info(url)
        
        if not video_url:
            bot.send_message(chat_id, f"❌ Could not process: {url}")
            return
            
        file_path = f"video_{chat_id}.mp4"
        bot.send_message(chat_id, f"⏳ Downloading: {title}...")
        
        if not download_file(video_url, file_path):
            bot.send_message(chat_id, f"❌ Download failed: {url}")
            return
            
        bot.send_message(chat_id, f"📤 Uploading: {title}...")
        loop.run_until_complete(
            send_video(chat_id, file_path, thumb_url, f"🎥 {title}")
        )
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Error processing {url}: {str(e)}")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    """Handle incoming messages with xHamster URLs."""
    text = message.text.strip()
    chat_id = message.chat.id
    
    # Extract all URLs from message
    urls = re.findall(r'https?://(?:www\.)?xhamster\.com/(?:videos|movies)/[^\s]+', text)
    
    if not urls:
        bot.send_message(chat_id, "Please send valid xHamster video URLs.")
        return
        
    if len(urls) > 5:
        bot.send_message(chat_id, "⚠️ For performance reasons, please send no more than 5 links at once.")
        urls = urls[:5]
        
    bot.send_message(chat_id, f"🔍 Found {len(urls)} video(s). Processing...")
    
    # Process each URL in parallel
    futures = []
    for url in urls:
        future = executor.submit(process_single_url, url, chat_id)
        futures.append(future)
        
    # Wait for all to complete
    for future in futures:
        try:
            future.result(timeout=300)  # 5 minutes per video max
        except Exception as e:
            print(f"Error in worker thread: {e}")
            continue

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
