import os
import re
import requests
import urllib.parse
import telebot
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

# Bot credentials
BOT_TOKEN = "8145114551:AAGOU9-3ZmRVxU91cPThM8vd932rNroR3WA"
API_ID = 22625636  # Replace with your API ID (integer)
API_HASH = "f71778a6e1e102f33ccc4aee3b5cc697"  # Replace with your API hash
SESSION_NAME = "xhamster_userbot"

bot = telebot.TeleBot(BOT_TOKEN)

# Telethon userbot
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
client.start()

def extract_slug(url):
    match = re.search(r"xhamster\.com\/videos\/([^\/]+)", url)
    return match.group(1) if match else None

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

        # Find best quality .mp4
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
        print("Error fetching API:", e)
        return None, None

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_message(message):
    url = message.text.strip()
    bot.reply_to(message, "⏳ Processing your video, please wait...")

    video_url, thumb = get_video_url(url)
    if not video_url:
        bot.send_message(message.chat.id, "❌ Couldn't find a valid video.")
        return

    file_name = "xhamster_video.mp4"

    try:
        # Download video
        r = requests.get(video_url, stream=True)
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # Send via Telethon (userbot)
        client.send_file(
            entity=message.chat.id,
            file=file_name,
            caption="🎥 Here's your video from xHamster"
        )

        os.remove(file_name)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed to send video. {e}")

bot.polling()
