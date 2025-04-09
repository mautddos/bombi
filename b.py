import os
import re
import requests
import urllib.parse
import telebot
from telebot import types
import asyncio
from telethon.sync import TelegramClient
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Telegram credentials
BOT_TOKEN = "8145114551:AAGOU9-3ZmRVxU91cPThM8vd932rNroR3WA"
API_ID = 22625636  # Replace with your API ID (integer)
API_HASH = "f71778a6e1e102f33ccc4aee3b5cc697"  # Replace with your API hash

bot = telebot.TeleBot(BOT_TOKEN)
client = TelegramClient("xhamster_userbot", API_ID, API_HASH)

# Thread pool for concurrent downloads
executor = ThreadPoolExecutor(max_workers=4)

# Dictionary to store video info temporarily
video_cache = {}

# Helper to extract slug
def extract_slug(url):
    match = re.search(r"xhamster\.com\/videos\/([^\/]+)", url)
    return match.group(1) if match else None

# Helper to get all available qualities
def get_video_qualities(xh_url):
    slug = extract_slug(xh_url)
    if not slug:
        return None, None, None

    encoded_url = urllib.parse.quote(f"https://xhamster.com/videos/{slug}")
    api_url = f"https://vkrdownloader.xyz/server/?api_key=vkrdownloader&vkr={encoded_url}"

    try:
        res = requests.get(api_url)
        data = res.json().get("data", {})
        thumbnail = data.get("thumbnail", "")
        title = data.get("title", "xHamster Video")
        downloads = data.get("downloads", [])

        # Filter and sort MP4 links by quality
        mp4_links = sorted(
            [d for d in downloads if d.get("url", "").endswith(".mp4")],
            key=lambda x: int(re.search(r"(\d+)p", x.get("format_id", "0p")).group(1)),
            reverse=True
        )

        return mp4_links, thumbnail, title

    except Exception as e:
        print("API Error:", e)
        return None, None, None

# Create quality selection keyboard
def create_quality_keyboard(qualities, cache_key):
    keyboard = types.InlineKeyboardMarkup()
    
    # Group qualities in rows of 2 buttons
    for i in range(0, len(qualities), 2):
        row = []
        for quality in qualities[i:i+2]:
            # Create a hash of the URL to use as callback data
            url_hash = hashlib.md5(quality['url'].encode()).hexdigest()
            btn = types.InlineKeyboardButton(
                text=f"{quality['format_id']}",
                callback_data=f"ql_{cache_key}_{url_hash}"
            )
            row.append(btn)
        keyboard.add(*row)
    
    return keyboard

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_message(message):
    url = message.text.strip()
    
    # Check if it's an xHamster URL
    if "xhamster.com/videos/" not in url:
        bot.reply_to(message, "❌ Please provide a valid xHamster video URL")
        return
    
    bot.reply_to(message, "🔍 Fetching video qualities...")
    
    qualities, thumbnail, title = get_video_qualities(url)
    
    if not qualities:
        bot.send_message(message.chat.id, "❌ Could not get video information.")
        return
    
    # Create a unique cache key for this request
    cache_key = hashlib.md5(f"{message.chat.id}_{message.message_id}".encode()).hexdigest()
    video_cache[cache_key] = {
        'qualities': qualities,
        'title': title
    }
    
    # Send thumbnail with quality selection buttons
    try:
        if thumbnail:
            bot.send_photo(
                chat_id=message.chat.id,
                photo=thumbnail,
                caption=f"🎬 {title}\n\nSelect video quality:",
                reply_markup=create_quality_keyboard(qualities, cache_key)
            )
        else:
            bot.send_message(
                chat_id=message.chat.id,
                text=f"🎬 {title}\n\nSelect video quality:",
                reply_markup=create_quality_keyboard(qualities, cache_key)
            )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error sending options: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('ql_'))
def handle_quality_selection(call):
    try:
        _, cache_key, url_hash = call.data.split('_', 2)
        video_info = video_cache.get(cache_key)
        
        if not video_info:
            bot.answer_callback_query(call.id, "❌ This request has expired. Please send the URL again.")
            return
        
        # Find the selected quality
        selected_quality = None
        for quality in video_info['qualities']:
            if hashlib.md5(quality['url'].encode()).hexdigest() == url_hash:
                selected_quality = quality
                break
        
        if not selected_quality:
            bot.answer_callback_query(call.id, "❌ Invalid quality selection")
            return
        
        # Edit the message to show download is starting
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⏳ Downloading {selected_quality['format_id']} quality video, please wait..."
        )
        
        # Use thread pool to handle download without blocking
        executor.submit(download_and_send_video, call.message.chat.id, selected_quality['url'])
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")

def download_and_send_video(chat_id, video_url):
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Download the video in chunks
        temp_file = f"temp_{chat_id}.mp4"
        
        with requests.get(video_url, stream=True) as r:
            r.raise_for_status()
            with open(temp_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        # Send the video using Telethon
        loop.run_until_complete(send_video(chat_id, temp_file))
        
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
    except Exception as e:
        error_msg = f"❌ Failed to send video. Error: {str(e)}"
        bot.send_message(chat_id, error_msg)
    finally:
        loop.close()

async def send_video(chat_id, file_path):
    async with TelegramClient("xhamster_userbot", API_ID, API_HASH) as client:
        await client.send_file(
            entity=chat_id,
            file=file_path,
            supports_streaming=True,
            caption="🎥 Here's your xHamster video"
        )

# Start the bot
print("Bot is running...")
bot.infinity_polling()
