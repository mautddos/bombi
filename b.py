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

# Start Telethon client
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(client.start())
print("✅ Telethon client connected!")

executor = ThreadPoolExecutor(max_workers=4)

video_data_cache = {}  # Store download links per message/user

# Extract slug
def extract_slug(url):
    match = re.search(r"xhamster\.com\/videos\/([^\/]+)", url)
    return match.group(1) if match else None

# Fetch video qualities
def get_video_options(xh_url):
    slug = extract_slug(xh_url)
    if not slug:
        return None, None, []

    encoded_url = urllib.parse.quote(f"https://xhamster.com/videos/{slug}")
    api_url = f"https://vkrdownloader.xyz/server/?api_key=vkrdownloader&vkr={encoded_url}"

    try:
        res = requests.get(api_url)
        data = res.json().get("data", {})
        thumbnail = data.get("thumbnail", "")
        downloads = data.get("downloads", [])

        options = sorted(
            [d for d in downloads if d.get("url", "").endswith(".mp4")],
            key=lambda x: int(re.search(r"(\d+)p", x.get("format_id", "0p")).group(1)),
            reverse=True
        )

        return data.get("title", "xHamster Video"), thumbnail, options
    except Exception as e:
        print("API error:", e)
        return None, None, []

# Async downloader
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

# Async handler
async def process_video_quality(message, video_url, quality_label):
    chat_id = message.chat.id
    file_name = f"xh_{chat_id}.mp4"
    downloading_msg = bot.send_message(chat_id, f"⏳ Downloading {quality_label} video...")

    success = await download_video_async(video_url, file_name)
    if not success:
        bot.edit_message_text("❌ Download failed.", chat_id, downloading_msg.message_id)
        return

    bot.edit_message_text("✅ Uploading to Telegram...", chat_id, downloading_msg.message_id)
    try:
        await client.send_file(chat_id, file=file_name, caption=f"🎥 Your {quality_label} video.")
        os.remove(file_name)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Upload failed: {e}")

# Handle video link
@bot.message_handler(func=lambda msg: msg.text.startswith("http"))
def handle_link(msg):
    title, thumb, options = get_video_options(msg.text.strip())
    if not options:
        bot.send_message(msg.chat.id, "❌ No video qualities found.")
        return

    # Cache video options
    video_data_cache[msg.chat.id] = {
        "options": options,
        "title": title
    }

    markup = InlineKeyboardMarkup()
    for opt in options:
        label = opt.get("format_id", "unknown")
        markup.add(InlineKeyboardButton(text=label, callback_data=f"q:{label}"))

    bot.send_message(msg.chat.id, f"🎬 *{title}*\nChoose a quality:", parse_mode="Markdown", reply_markup=markup)

# Handle button click
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

    # Run async download/upload
    executor.submit(lambda: loop.run_until_complete(
        process_video_quality(call.message, video_url, quality)
    ))

# Start bot
print("🚀 Bot with quality selection is running...")
bot.polling()
