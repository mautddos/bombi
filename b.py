import os
import re
import requests
import urllib.parse
import telebot
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Telegram credentials
BOT_TOKEN = "8145114551:AAGOU9-3ZmRVxU91cPThM8vd932rNroR3WA"
API_ID = 22625636  # integer
API_HASH = "f71778a6e1e102f33ccc4aee3b5cc697"

bot = telebot.TeleBot(BOT_TOKEN)
client = TelegramClient(StringSession(), API_ID, API_HASH)  # Using StringSession for persistence

# Start Telethon client in the background
async def start_client():
    await client.start()
    print("✅ Telethon client connected successfully!")

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(start_client())

# Helper to extract slug
def extract_slug(url):
    match = re.search(r"xhamster\.com\/videos\/([^\/]+)", url)
    return match.group(1) if match else None

# Helper to get best .mp4
def get_video_url(xh_url):
    slug = extract_slug(xh_url)
    if not slug:
        return None, None

    encoded_url = urllib.parse.quote(f"https://xhamster.com/videos/{slug}")
    api_url = f"https://vkrdownloader.xyz/server/?api_key=vkrdownloader&vkr={encoded_url}"

    try:
        res = requests.get(api_url)
        data = res.json().get("data", {})
        thumbnail = data.get("thumbnail", "")
        downloads = data.get("downloads", [])

        mp4_links = sorted(
            [d for d in downloads if d.get("url", "").endswith(".mp4")],
            key=lambda x: int(re.search(r"(\d+)p", x.get("format_id", "0p")).group(1)),
            reverse=True
        )

        if mp4_links:
            return mp4_links[0]["url"], thumbnail
        else:
            return None, None

    except Exception as e:
        print("API Error:", e)
        return None, None

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_message(message):
    url = message.text.strip()
    bot.reply_to(message, "⏳ Downloading your video, please wait...")

    video_url, thumb = get_video_url(url)
    if not video_url:
        bot.send_message(message.chat.id, "❌ Could not get video link.")
        return

    file_name = "video.mp4"
    try:
        # Download video
        r = requests.get(video_url, stream=True)
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # Send video using Telethon (ensure client is connected)
        async def send_video_async():
            try:
                if not client.is_connected():
                    await client.connect()
                await client.send_file(
                    entity=message.chat.id,
                    file=file_name,
                    caption="🎥 Here's your xHamster video."
                )
            except Exception as e:
                print(f"Error sending video: {e}")
                bot.send_message(message.chat.id, f"❌ Failed to send video: {e}")

        loop.run_until_complete(send_video_async())
        os.remove(file_name)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed to process video: {e}")

# Start polling
print("Bot is running...")
bot.polling()
