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
import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from concurrent.futures import ThreadPoolExecutor
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import subprocess
from PIL import Image
from tqdm import tqdm

# Telegram credentials
BOT_TOKEN = "8145114551:AAGOU9-3ZmRVxU91cPThM8vd932rNroR3WA"
API_ID = 22625636
API_HASH = "f71778a6e1e102f33ccc4aee3b5cc697"

bot = telebot.TeleBot(BOT_TOKEN)
client = TelegramClient(StringSession(), API_ID, API_HASH)

# Bot start time for uptime calculation
BOT_START_TIME = time.time()

# Configuration
MAX_CONCURRENT_DOWNLOADS = 3  # Limit concurrent downloads
DOWNLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB chunks for download
VIDEO_UPLOAD_CHUNK_SIZE = 512 * 1024  # 512KB chunks for upload
MAX_LINKS_PER_MESSAGE = 5  # Maximum links to process at once

# Async function to start Telethon client as bot
async def start_telethon():
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Telethon client connected!")

loop = asyncio.get_event_loop()
loop.run_until_complete(start_telethon())

executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS)
video_data_cache = {}  # Store per-user quality options

class DownloadProgress:
    def __init__(self, message, total_size):
        self.message = message
        self.total_size = total_size
        self.start_time = time.time()
        self.last_update = 0
        self.progress_message = None
    
    async def update(self, downloaded):
        current_time = time.time()
        # Only update every 2 seconds to avoid spamming
        if current_time - self.last_update < 2:
            return
        
        self.last_update = current_time
        elapsed = current_time - self.start_time
        speed = downloaded / elapsed if elapsed > 0 else 0
        
        # Calculate percentage and ETA
        percent = (downloaded / self.total_size) * 100
        remaining_bytes = self.total_size - downloaded
        eta = remaining_bytes / speed if speed > 0 else 0
        
        # Format sizes
        def sizeof_fmt(num):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if abs(num) < 1024.0:
                    return "%3.1f %s" % (num, unit)
                num /= 1024.0
            return "%.1f %s" % (num, 'TB')
        
        progress_text = (
            f"⬇️ Downloading: {percent:.1f}%\n"
            f"📁 Size: {sizeof_fmt(downloaded)} / {sizeof_fmt(self.total_size)}\n"
            f"⚡ Speed: {sizeof_fmt(speed)}/s\n"
            f"⏳ ETA: {datetime.timedelta(seconds=int(eta))}"
        )
        
        try:
            if self.progress_message:
                await bot.edit_message_text(
                    progress_text,
                    chat_id=self.message.chat.id,
                    message_id=self.progress_message.message_id
                )
            else:
                self.progress_message = await bot.send_message(
                    self.message.chat.id,
                    progress_text
                )
        except Exception as e:
            print("Progress update error:", e)

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
        res = requests.get(api_url, timeout=10)
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
                f"-vframes 1 -q:v 2 -pix_fmt yuv420p "
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

# Async downloader with progress tracking
async def download_video_async(video_url, file_name, progress_callback=None):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as resp:
                if resp.status == 200:
                    total_size = int(resp.headers.get('content-length', 0))
                    
                    with open(file_name, 'wb') as f:
                        downloaded = 0
                        async for chunk in resp.content.iter_chunked(DOWNLOAD_CHUNK_SIZE):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                await progress_callback(downloaded)
                    
                    return True
    except Exception as e:
        print("Download error:", e)
    return False

# Async handler with improved upload
async def process_video_quality(message, video_url, quality_label):
    chat_id = message.chat.id
    file_name = f"xh_{chat_id}_{int(time.time())}.mp4"
    
    # Create progress tracker
    async def get_total_size():
        async with aiohttp.ClientSession() as session:
            async with session.head(video_url) as resp:
                return int(resp.headers.get('content-length', 0))
    
    total_size = await get_total_size()
    progress = DownloadProgress(message, total_size)
    
    # Download with progress
    downloading_msg = await bot.send_message(chat_id, "⏳ Starting download...")
    success = await download_video_async(video_url, file_name, progress.update)
    
    if not success:
        await bot.edit_message_text("❌ Download failed.", chat_id, downloading_msg.message_id)
        return

    # Generate and send screenshots
    screenshot_msg = await bot.send_message(chat_id, "📸 Generating screenshots...")
    screenshot_dir = await generate_screenshots(file_name, chat_id)
    
    if screenshot_dir:
        await bot.edit_message_text("🖼️ Uploading screenshots...", chat_id, screenshot_msg.message_id)
        try:
            # Send screenshots as album
            screenshot_files = sorted(
                [f for f in os.listdir(screenshot_dir) if f.endswith('.jpg')],
                key=lambda x: int(x.split('_')[1].split('.')[0])
            
            # Split into chunks of 10 to avoid flooding
            for chunk in [screenshot_files[i:i+10] for i in range(0, len(screenshot_files), 10)]:
                media = []
                for i, screenshot in enumerate(chunk):
                    media.append(telebot.types.InputMediaPhoto(
                        open(f"{screenshot_dir}/{screenshot}", 'rb'),
                        caption=f"Screenshot {i+1}" if i == 0 else ""
                    ))
                
                await bot.send_media_group(chat_id, media)
            
            # Clean up screenshots
            for f in os.listdir(screenshot_dir):
                os.remove(f"{screenshot_dir}/{f}")
            os.rmdir(screenshot_dir)
        except Exception as e:
            print("Screenshot upload error:", e)
    
    # Upload video with progress
    upload_progress = DownloadProgress(message, os.path.getsize(file_name))
    upload_progress.progress_message = await bot.send_message(chat_id, "⬆️ Starting video upload...")
    
    try:
        # Use telethon for faster uploads with progress
        def callback(current, total):
            loop.run_until_complete(upload_progress.update(current))
        
        file = await client.upload_file(
            file_name,
            part_size_kb=VIDEO_UPLOAD_CHUNK_SIZE // 1024,
            progress_callback=callback
        )
        
        await client.send_file(
            chat_id, 
            file=file,
            caption=f"🎥 Your {quality_label} video.\n⚡ @XHamsterDownloaderBot",
            supports_streaming=True
        )
        
        if os.path.exists(file_name):
            os.remove(file_name)
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Upload failed: {e}")

# Process multiple links
async def process_multiple_links(message, urls):
    chat_id = message.chat.id
    valid_urls = []
    
    # Validate URLs
    for url in urls[:MAX_LINKS_PER_MESSAGE]:
        if extract_slug(url):
            valid_urls.append(url)
    
    if not valid_urls:
        await bot.send_message(chat_id, "❌ No valid xHamster URLs found.")
        return
    
    status_msg = await bot.send_message(chat_id, f"🔍 Found {len(valid_urls)} valid links. Processing...")
    
    for i, url in enumerate(valid_urls):
        try:
            title, thumb, options = get_video_options(url)
            if not options:
                continue
                
            video_data_cache[f"{chat_id}_{i}"] = {
                "options": options,
                "title": title
            }
            
            markup = InlineKeyboardMarkup()
            for opt in options:
                label = opt.get("format_id", "unknown")
                markup.add(InlineKeyboardButton(text=label, callback_data=f"q:{i}:{label}"))
            
            caption = f"🎬 {title}\nLink {i+1}/{len(valid_urls)}\nChoose a quality:"
            
            if thumb:
                try:
                    await bot.send_photo(
                        chat_id, 
                        thumb, 
                        caption=caption, 
                        reply_markup=markup
                    )
                    continue
                except:
                    pass
            
            await bot.send_message(chat_id, caption, reply_markup=markup)
            
        except Exception as e:
            print(f"Error processing URL {url}:", e)
    
    await bot.delete_message(chat_id, status_msg.message_id)

# Status command
@bot.message_handler(commands=['status'])
def status_command(message):
    # System stats
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    
    # Bot stats
    uptime_seconds = time.time() - BOT_START_TIME
    uptime_str = str(datetime.timedelta(seconds=int(uptime_seconds)))
    
    # Create status message
    status_msg = f"""
🤖 *Bot Status Report* 🤖

*🛠️ System Resources:*
• CPU Usage: {cpu_usage}%
• Memory Usage: {memory_usage}%
• Disk Usage: {disk_usage}%

*⏱️ Bot Runtime:*
• Uptime: {uptime_str}

*⚡ Performance:*
• Active Threads: {executor._work_queue.qsize()}
• Max Workers: {executor._max_workers}

💾 *Cache Info:*
• Cached Videos: {len(video_data_cache)}

🔧 *Version:*
• Advanced XHamster Downloader v3.0
• Multiple link support
• Progress tracking
"""
    bot.send_message(message.chat.id, status_msg, parse_mode="Markdown")

# Start command
@bot.message_handler(commands=['start'])
def start_command(message):
    start_msg = """
🌟 *Welcome to XHamster Downloader Bot* 🌟

Send me xHamster video links and I'll download them for you with multiple quality options!

⚡ *Features:*
• Multiple quality options
• Fast parallel downloads
• 20 screenshots per video
• Upload/download progress tracking
• Multiple link support (up to {MAX_LINKS_PER_MESSAGE} at once)

📌 *How to use:*
Just send me xHamster video URLs (one per line or space separated) and I'll handle the rest!

🔧 *Commands:*
/start - Show this message
/status - Show bot status
""".format(MAX_LINKS_PER_MESSAGE=MAX_LINKS_PER_MESSAGE)
    bot.send_message(message.chat.id, start_msg, parse_mode="Markdown")

# Handle video links
@bot.message_handler(func=lambda msg: any(extract_slug(url) for url in msg.text.split()))
def handle_links(msg):
    urls = []
    for word in msg.text.split():
        if extract_slug(word):
            urls.append(word)
    
    if len(urls) > 1:
        executor.submit(lambda: loop.run_until_complete(process_multiple_links(msg, urls)))
    else:
        title, thumb, options = get_video_options(urls[0])
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
            markup.add(InlineKeyboardButton(text=label, callback_data=f"q:0:{label}"))

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
    parts = call.data.split(":")
    if len(parts) != 3:
        bot.answer_callback_query(call.id, "Invalid selection.")
        return
    
    index, quality = parts[1], parts[2]
    user_id = call.message.chat.id
    cache_key = f"{user_id}_{index}" if index != "0" else user_id
    
    options = video_data_cache.get(cache_key, {}).get("options", [])
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
    bot.send_message(msg.chat.id, "Please send valid xHamster video URL(s) or use /start to see options.")

# Start bot
print("🚀 Advanced XHamster Downloader Bot is running...")
bot.polling(none_stop=True, interval=0)
