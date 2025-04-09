import os
import re
import urllib.parse
import asyncio
import aiohttp
import aiofiles
import subprocess
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from concurrent.futures import ThreadPoolExecutor
from telethon import TelegramClient
from telethon.sessions import StringSession

# Telegram credentials
BOT_TOKEN = "8145114551:AAGOU9-3ZmRVxU91cPThM8vd932rNroR3WA"
API_ID = 22625636
API_HASH = "f71778a6e1e102f33ccc4aee3b5cc697"

bot = telebot.TeleBot(BOT_TOKEN)
client = TelegramClient(StringSession(), API_ID, API_HASH)

# Start Telethon
async def start_client():
    await client.start(bot_token=BOT_TOKEN)
loop = asyncio.get_event_loop()
loop.run_until_complete(start_client())

executor = ThreadPoolExecutor()
video_data_cache = {}

# Extract slug
def extract_slug(url):
    match = re.search(r"xhamster\.com\/videos\/([^\/]+)", url)
    return match.group(1) if match else None

# Get video options
def get_video_options(xh_url):
    slug = extract_slug(xh_url)
    if not slug:
        return None, None, []

    encoded_url = urllib.parse.quote(f"https://xhamster.com/videos/{slug}")
    api_url = f"https://vkrdownloader.xyz/server/?api_key=vkrdownloader&vkr={encoded_url}"

    try:
        res = requests.get(api_url)
        data = res.json().get("data", {})
        title = data.get("title", "xHamster Video")
        thumbnail = data.get("thumbnail", "")
        downloads = data.get("downloads", [])

        options = sorted(
            [d for d in downloads if d.get("url", "").endswith(".mp4")],
            key=lambda x: int(re.search(r"(\d+)p", x.get("format_id", "0p")).group(1)),
            reverse=True
        )

        for opt in options:
            opt["thumbnail"] = thumbnail

        return title, thumbnail, options
    except Exception as e:
        print("API error:", e)
        return None, None, []

# Optimize video for Telegram
def optimize_video(input_file, output_file):
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", input_file,
            "-c", "copy", "-movflags", "+faststart", output_file
        ], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print("FFmpeg error:", e)
        return False

# Async download
async def download_file(url, path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    async with aiofiles.open(path, 'wb') as f:
                        await f.write(await r.read())
                        return True
    except Exception as e:
        print(f"Download failed: {e}")
    return False

# Final video process
async def process_video(message, video_url, quality, thumbnail_url):
    chat_id = message.chat.id
    base = f"xh_{chat_id}"
    video_file = f"{base}.mp4"
    thumb_file = f"{base}.jpg"
    optimized_file = f"{base}_opt.mp4"

    bot.send_message(chat_id, f"⏳ Downloading {quality} video...")

    # Download video + thumbnail
    await download_file(video_url, video_file)
    await download_file(thumbnail_url, thumb_file)

    # Re-encode for Telegram
    if not optimize_video(video_file, optimized_file):
        bot.send_message(chat_id, "❌ Video optimization failed.")
        return

    try:
        await client.send_file(
            chat_id,
            file=optimized_file,
            caption=f"🎬 Your {quality} video.",
            thumb=thumb_file,
            supports_streaming=True
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ Upload error: {e}")
    finally:
        for f in [video_file, thumb_file, optimized_file]:
            if os.path.exists(f):
                os.remove(f)

# Handle video links
@bot.message_handler(func=lambda msg: msg.text.startswith("http"))
def handle_link(msg):
    title, thumb, options = get_video_options(msg.text.strip())
    if not options:
        bot.send_message(msg.chat.id, "❌ No video found.")
        return

    video_data_cache[msg.chat.id] = {"options": options, "title": title}
    markup = InlineKeyboardMarkup()

    for opt in options:
        label = opt.get("format_id", "unknown")
        markup.add(InlineKeyboardButton(text=label, callback_data=f"q:{label}"))

    bot.send_message(msg.chat.id, f"🎬 *{title}*\nChoose video quality:", parse_mode="Markdown", reply_markup=markup)

# Handle quality selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("q:"))
def handle_quality(call):
    quality = call.data.split("q:")[1]
    user_id = call.message.chat.id
    options = video_data_cache.get(user_id, {}).get("options", [])
    selected = next((o for o in options if o.get("format_id") == quality), None)

    if not selected:
        bot.answer_callback_query(call.id, "Quality not found.")
        return

    bot.edit_message_reply_markup(user_id, call.message.message_id)
    executor.submit(lambda: loop.run_until_complete(
        process_video(call.message, selected.get("url"), quality, selected.get("thumbnail"))
    ))

# Start bot
print("🚀 Video bot running with ffmpeg streaming and thumbnail preview...")
bot.polling()
