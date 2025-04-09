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
from collections import deque
from typing import Dict, Deque, Optional
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from concurrent.futures import ThreadPoolExecutor
from telethon import TelegramClient
from telethon.sessions import StringSession
import subprocess
from PIL import Image

# Telegram credentials
BOT_TOKEN ="8145114551:AAGOU9-3ZmRVxU91cPThM8vd932rNroR3WA"
API_ID = 22625636
API_HASH = "f71778a6e1e102f33ccc4aee3b5cc697"

bot = telebot.TeleBot(BOT_TOKEN)
client = TelegramClient(StringSession(), API_ID, API_HASH)

# Bot start time for uptime calculation
BOT_START_TIME = time.time()

# Global task management
task_queue: Deque = deque()
current_tasks: Dict[int, asyncio.Task] = {}
MAX_PARALLEL_DOWNLOADS = 3  # Maximum parallel downloads allowed
user_status: Dict[int, Dict] = {}  # Track user download status

# Async function to start Telethon client as bot
async def start_telethon():
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Telethon client connected!")

loop = asyncio.get_event_loop()
loop.run_until_complete(start_telethon())

executor = ThreadPoolExecutor(max_workers=4)
video_data_cache = {}  # Store per-user quality options

async def process_queue():
    """Task queue processor that manages parallel downloads"""
    while True:
        if task_queue and len(current_tasks) < MAX_PARALLEL_DOWNLOADS:
            chat_id, task_func, quality = task_queue.popleft()
            
            # If user already has a download in progress, put it back in queue
            if chat_id in current_tasks:
                task_queue.appendleft((chat_id, task_func, quality))
            else:
                # Update user status
                user_status[chat_id] = {
                    'status': 'downloading',
                    'quality': quality,
                    'start_time': time.time()
                }
                
                task = asyncio.create_task(task_func())
                current_tasks[chat_id] = task
                
                # Add callback to clean up after task completes
                def cleanup(future, cid=chat_id):
                    current_tasks.pop(cid, None)
                    user_status.pop(cid, None)
                
                task.add_done_callback(cleanup)
                
                # Notify user their download is starting
                try:
                    await bot.send_message(chat_id, f"🚀 Starting your {quality} download now!")
                except:
                    pass
        
        await asyncio.sleep(1)

# Start queue processor when bot starts
loop.create_task(process_queue())

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
    
    try:
        downloading_msg = await bot.send_message(chat_id, f"⏳ Downloading {quality_label} video...")
        
        success = await download_video_async(video_url, file_name)
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
        
        # Upload video
        await bot.edit_message_text("✅ Uploading to Telegram...", chat_id, downloading_msg.message_id)
        try:
            await client.send_file(
                chat_id, 
                file=file_name, 
                caption=f"🎥 Your {quality_label} video.\n⚡ @semxi_suxbot",
                supports_streaming=True
            )
        except Exception as e:
            await bot.send_message(chat_id, f"❌ Upload failed: {e}")
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)
    except Exception as e:
        print("Error in video processing:", e)
        await bot.send_message(chat_id, "❌ An error occurred during processing.")

# Status command with queue information
@bot.message_handler(commands=['status'])
def status_command(message):
    # System stats
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    
    # Bot stats
    uptime_seconds = time.time() - BOT_START_TIME
    uptime_str = str(datetime.timedelta(seconds=int(uptime_seconds)))
    
    # Queue information
    active_downloads = len(current_tasks)
    queued_downloads = len(task_queue)
    
    # Create status message
    status_msg = f"""
🤖 *Bot Status Report* 🤖

*🛠️ System Resources:*
• CPU Usage: {cpu_usage}%
• Memory Usage: {memory_usage}%
• Disk Usage: {disk_usage}%

*⏱️ Bot Runtime:*
• Uptime: {uptime_str}

*📥 Download Queue:*
• Active Downloads: {active_downloads}/{MAX_PARALLEL_DOWNLOADS}
• Waiting in Queue: {queued_downloads}

*⚡ Performance:*
• Max Workers: {executor._max_workers}

🔧 *Version:*
• Advanced XHamster Downloader v2.1 with Queue System
"""
    bot.send_message(message.chat.id, status_msg, parse_mode="Markdown")

# Queue position command
@bot.message_handler(commands=['queue'])
def queue_command(message):
    chat_id = message.chat.id
    
    # Check if user has any active or queued downloads
    active_position = None
    queue_position = None
    
    # Check if currently downloading
    if chat_id in current_tasks:
        status = user_status.get(chat_id, {})
        elapsed = int(time.time() - status.get('start_time', time.time()))
        bot.send_message(chat_id, f"🔍 Your {status.get('quality', '')} download is currently processing ({elapsed}s elapsed)")
        return
    
    # Check queue position
    queue_list = [t[0] for t in task_queue]
    if chat_id in queue_list:
        position = queue_list.index(chat_id) + 1
        bot.send_message(chat_id, f"📊 Your download is #{position} in the queue")
    else:
        bot.send_message(chat_id, "ℹ️ You don't have any downloads in queue")

# Cancel command
@bot.message_handler(commands=['cancel'])
def cancel_command(message):
    chat_id = message.chat.id
    
    if chat_id in current_tasks:
        current_tasks[chat_id].cancel()
        bot.send_message(chat_id, "❌ Your current download has been cancelled")
    elif any(t[0] == chat_id for t in task_queue):
        # Remove all queued tasks for this user
        task_queue = deque(t for t in task_queue if t[0] != chat_id)
        bot.send_message(chat_id, "❌ Your queued download has been removed")
    else:
        bot.send_message(chat_id, "ℹ️ You don't have any active or queued downloads")

# Start command
@bot.message_handler(commands=['start'])
def start_command(message):
    start_msg = """
🌟 *Welcome to XHamster Downloader Bot* 🌟

Send me a xHamster video link and I'll download it for you with multiple quality options!

⚡ *Features:*
• Multiple quality options
• Automatic queue system
• Cancel anytime with /cancel
• Check queue position with /queue
• 20 screenshots per video

📌 *How to use:*
1. Send xHamster video URL
2. Select quality
3. Your download will automatically process when ready

🔧 *Commands:*
/start - Show this message
/status - Show bot status
/queue - Check your queue position
/cancel - Cancel your download
"""
    bot.send_message(message.chat.id, start_msg, parse_mode="Markdown")

# Handle video link
@bot.message_handler(func=lambda msg: msg.text.startswith("http"))
def handle_link(msg):
    # Check if user already has active download
    if msg.chat.id in current_tasks:
        bot.send_message(msg.chat.id, "⚠️ You already have a download in progress. Use /cancel if you want to stop it.")
        return
    
    title, thumb, options = get_video_options(msg.text.strip())
    if not options:
        bot.send_message(msg.chat.id, "❌ No video qualities found.")
        return

    video_data_cache[msg.chat.id] = {
        "options": options,
        "title": title,
        "url": msg.text.strip()
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
    
    # Add cancel button
    cancel_markup = InlineKeyboardMarkup()
    cancel_markup.add(InlineKeyboardButton("❌ Cancel Download", callback_data=f"cancel:{user_id}"))
    
    # Get queue position
    queue_pos = sum(1 for t in task_queue if t[0] == user_id) + 1
    if queue_pos > 1:
        queue_info = f" (Position in queue: {queue_pos})"
    else:
        queue_info = ""
    
    bot.send_message(
        user_id, 
        f"📥 Added {quality} download to queue{queue_info}",
        reply_markup=cancel_markup
    )

    # Add task to queue
    task_queue.append((
        user_id,
        lambda: process_video_quality(call.message, video_url, quality),
        quality
    ))

# Handle cancel button
@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel:"))
def handle_cancel_button(call):
    user_id = int(call.data.split(":")[1])
    
    if user_id in current_tasks:
        current_tasks[user_id].cancel()
        bot.answer_callback_query(call.id, "Download cancelled")
        bot.send_message(user_id, "❌ Your download has been cancelled")
    elif any(t[0] == user_id for t in task_queue):
        # Remove all queued tasks for this user
        global task_queue
        task_queue = deque(t for t in task_queue if t[0] != user_id)
        bot.answer_callback_query(call.id, "Queued download removed")
        bot.send_message(user_id, "❌ Your queued download has been removed")
    else:
        bot.answer_callback_query(call.id, "No download to cancel")

# Error handler
@bot.message_handler(func=lambda msg: True)
def handle_other_messages(msg):
    bot.send_message(msg.chat.id, "Please send a valid xHamster video URL or use /start to see options.")

# Start bot
print("🚀 Advanced XHamster Downloader Bot is running with queue system...")
bot.polling(none_stop=True, interval=0)
