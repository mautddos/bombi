import os
import re
import urllib.parse
import asyncio
import aiohttp
import aiofiles
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

# Async function to start Telethon client
async def start_telethon():
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Telethon client connected!")

loop = asyncio.get_event_loop()
loop.run_until_complete(start_telethon())

executor = ThreadPoolExecutor(max_workers=4)
video_data_cache = {}  # Store per-user video options

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

        # Save thumbnail URL in each option
        for opt in options:
            opt["thumbnail"] = thumbnail

        return title, thumbnail, options
    except Exception as e:
        print("API error:", e)
        return None, None, []

# Async download
async def download_video_async(video_url, file_name):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(file_name, mode='wb')
                    await f.write(await resp.read())
                    await f.close()
                    return True
    except Exception as e:
        print("Download error:", e)
    return False

# Process video with thumbnail
async def process_video_quality(message, video_url, quality_label):
    chat_id = message.chat.id
    file_name = f"xh_{chat_id}.mp4"
    thumb_file = f"xh_thumb_{chat_id}.jpg"
    downloading_msg = bot.send_message(chat_id, f"⏳ Downloading {quality_label} video...")

    # Get thumbnail URL
    thumb_url = video_data_cache.get(chat_id, {}).get("options", [])[0].get("thumbnail", "")

    try:
        if thumb_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumb_url) as response:
                    if response.status == 200:
                        f = await aiofiles.open(thumb_file, mode='wb')
                        await f.write(await response.read())
                        await f.close()
    except Exception as e:
        print("Thumbnail download error:", e)
        thumb_file = None

    # Download the video
    success = await download_video_async(video_url, file_name)
    if not success:
        bot.edit_message_text("❌ Video download failed.", chat_id, downloading_msg.message_id)
        return

    bot.edit_message_text("✅ Uploading to Telegram...", chat_id, downloading_msg.message_id)

    try:
        await client.send_file(
            chat_id,
            file=file_name,
            caption=f"🎥 Your {quality_label} video.",
            thumb=thumb_file if os.path.exists(thumb_file) else None,
            supports_streaming=True
        )
        os.remove(file_name)
        if os.path.exists(thumb_file):
            os.remove(thumb_file)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Upload failed: {e}")

# Handle video link
@bot.message_handler(func=lambda msg: msg.text.startswith("http"))
def handle_link(msg):
    title, thumb, options = get_video_options(msg.text.strip())
    if not options:
        bot.send_message(msg.chat.id, "❌ No video qualities found.")
        return

    video_data_cache[msg.chat.id] = {
        "options": options,
        "title": title
    }

    markup = InlineKeyboardMarkup()
    for opt in options:
        label = opt.get("format_id", "unknown")
        markup.add(InlineKeyboardButton(text=label, callback_data=f"q:{label}"))

    bot.send_message(msg.chat.id, f"🎬 *{title}*\nChoose a quality:", parse_mode="Markdown", reply_markup=markup)

# Handle quality button
@bot.callback_query_handler(func=lambda call: call.data.startswith("q:"))
def handle_quality_choice(call):
    quality = call.data.split("q:")[1]
    user_id = call.message.chat.id
    options = video_data_cache.get(user_id, {}).get("options", [])

    selected = next((o for o in options if o.get("format_id") == quality), None)
    if not selected:
        bot.answer_callback_query(call.id, "Quality not found.")
        return

    video_url = selected.get("url")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.send_message(call.message.chat.id, f"📥 Preparing {quality} download...")

    executor.submit(lambda: loop.run_until_complete(
        process_video_quality(call.message, video_url, quality)
    ))

# Start bot
print("🚀 Bot with thumbnail support is running...")
bot.polling()
