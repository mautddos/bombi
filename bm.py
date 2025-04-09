import os
import re
import urllib.parse
import asyncio
import aiohttp
import aiofiles
import requests
import telebot
import time
import psutil
import datetime  # Fixed import
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from concurrent.futures import ThreadPoolExecutor
from telethon import TelegramClient
from telethon.sessions import StringSession
import subprocess
from PIL import Image

# Telegram credentials
BOT_TOKEN = "8145114551:AAGOU9-3ZmRVxU91cPThM8vd932rNroR3WA"
API_ID = 22625636
API_HASH = "f71778a6e1e102f33ccc4aee3b5cc697"

bot = telebot.TeleBot(BOT_TOKEN)
client = TelegramClient(StringSession(), API_ID, API_HASH)

# Bot start time for uptime calculation
BOT_START_TIME = time.time()

# Async function to start Telethon client as bot
async def start_telethon():
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Telethon client connected!")

loop = asyncio.get_event_loop()
loop.run_until_complete(start_telethon())

executor = ThreadPoolExecutor(max_workers=4)
video_data_cache = {}  # Store per-user quality options

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
        return title, thumbnail, options
    except Exception as e:
        print("API error:", e)
        return None, None, []

# Generate screenshots from video
async def generate_screenshots(video_path, chat_id):
    try:
        # Create screenshots directory
        screenshot_dir = f"screenshots_{chat_id}"
        os.makedirs(screenshot_dir, exist_ok=True)
        
        # Get video duration
        cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {video_path}"
        duration = float(subprocess.check_output(cmd, shell=True).decode('utf-8').strip())
        
        # Calculate screenshot intervals (20 screenshots)
        intervals = [i * (duration / 20) for i in range(1, 21)]
        
        # Generate screenshots with proper pixel format
        for i, interval in enumerate(intervals):
            output_path = f"{screenshot_dir}/screenshot_{i+1}.jpg"
            cmd = (
                f"ffmpeg -ss {interval} -i {video_path} "
                f"-vframes 1 -q:v 2 -pix_fmt yuv420p "  # Added proper pixel format
                f"{output_path} -y"
            )
            subprocess.run(cmd, shell=True, check=True, stderr=subprocess.DEVNULL)
            
            # Optimize image if it exists
            if os.path.exists(output_path):
                with Image.open(output_path) as img:
                    img.save(output_path, "JPEG", quality=85)
            else:
                print(f"Screenshot not generated: {output_path}")
        
        return screenshot_dir
    except Exception as e:
        print("Screenshot generation error:", e)
        return None

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

    # Generate and send screenshots
    screenshot_msg = bot.send_message(chat_id, "📸 Generating screenshots...")
    screenshot_dir = await generate_screenshots(file_name, chat_id)
    
    if screenshot_dir:
        bot.edit_message_text("🖼️ Uploading screenshots...", chat_id, screenshot_msg.message_id)
        try:
            # Send screenshots as album
            screenshot_files = sorted(
                [f for f in os.listdir(screenshot_dir) if f.endswith('.jpg')],
                key=lambda x: int(x.split('_')[1].split('.')[0])
            )
            
            # Split into chunks of 10 to avoid flooding
            for chunk in [screenshot_files[i:i+10] for i in range(0, len(screenshot_files), 10)]:
                media = []
                for i, screenshot in enumerate(chunk):
                    media.append(telebot.types.InputMediaPhoto(
                        open(f"{screenshot_dir}/{screenshot}", 'rb'),
                        caption=f"Screenshot {i+1}" if i == 0 else ""
                    ))
                
                bot.send_media_group(chat_id, media)
            
            # Clean up screenshots
            for f in os.listdir(screenshot_dir):
                os.remove(f"{screenshot_dir}/{f}")
            os.rmdir(screenshot_dir)
        except Exception as e:
            print("Screenshot upload error:", e)
    
    # Upload video
    bot.edit_message_text("✅ Uploading to Telegram...", chat_id, downloading_msg.message_id)
    try:
        await client.send_file(
            chat_id, 
            file=file_name, 
            caption=f"🎥 Your {quality_label} video.\n⚡ @XHamsterDownloaderBot",
            supports_streaming=True
        )
        if os.path.exists(file_name):
            os.remove(file_name)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Upload failed: {e}")

# Status command
@bot.message_handler(commands=['status'])
def status_command(message):
    # System stats
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    
    # Bot stats
    uptime_seconds = time.time() - BOT_START_TIME
    uptime_str = str(datetime.timedelta(seconds=int(uptime_seconds)))  # Fixed datetime usage
    
    # Create status message
    status_msg = f"""
🤖 *Bot Status Report* 🤖

*🛠️ System Resources:*
• CPU Usage: {cpu_usage}%
• Memory Usage: {memory_usage}%
• Disk Usage: {disk_usage}%

*⏱️ Bot Runtime:*
• Uptime: {uptime_str}
• Ping: Calculating...

*⚡ Performance:*
• Active Threads: {executor._work_queue.qsize()}
• Max Workers: {executor._max_workers}

💾 *Cache Info:*
• Cached Videos: {len(video_data_cache)}

🔧 *Version:*
• Advanced XHamster Downloader v2.0
"""
    bot.send_message(message.chat.id, status_msg, parse_mode="Markdown")

# Start command
@bot.message_handler(commands=['start'])
def start_command(message):
    start_msg = """
🌟 *Welcome to XHamster Downloader Bot* 🌟

Send me a xHamster video link and I'll download it for you with multiple quality options!

⚡ *Features:*
• Multiple quality options
• Fast downloads
• 20 screenshots per video
• Stable and reliable

📌 *How to use:*
Just send me a xHamster video URL and I'll handle the rest!

🔧 *Commands:*
/start - Show this message
/status - Show bot status
"""
    bot.send_message(message.chat.id, start_msg, parse_mode="Markdown")

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

    if thumb:
        try:
            bot.send_photo(
                msg.chat.id, 
                thumb, 
                caption=f"🎬 *{title}*\nChoose a quality:", 
                parse_mode="Markdown", 
                reply_markup=markup
            )
            return
        except:
            pass
    
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

    executor.submit(lambda: loop.run_until_complete(
        process_video_quality(call.message, video_url, quality)
    ))

# Error handler
@bot.message_handler(func=lambda msg: True)
def handle_other_messages(msg):
    bot.send_message(msg.chat.id, "Please send a valid xHamster video URL or use /start to see options.")

# Start bot
print("🚀 Advanced XHamster Downloader Bot is running...")
bot.polling(none_stop=True, interval=0)
