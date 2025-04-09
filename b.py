import os
import re
import requests
import telebot
from telebot import types
import hashlib
import json
from datetime import datetime, timedelta

# Telegram bot token
BOT_TOKEN = "8145114551:AAGOU9-3ZmRVxU91cPThM8vd932rNroR3WA"
bot = telebot.TeleBot(BOT_TOKEN)

# Video request cache with expiration
video_requests = {}

class VideoRequest:
    def __init__(self, qualities, title):
        self.qualities = qualities
        self.title = title
        self.timestamp = datetime.now()
    
    def is_expired(self):
        return datetime.now() - self.timestamp > timedelta(minutes=10)

def extract_slug(url):
    match = re.search(r"xhamster\.com\/videos\/([^\/]+)", url)
    return match.group(1) if match else None

def get_video_qualities(url):
    try:
        slug = extract_slug(url)
        if not slug:
            return None, None
        
        api_url = f"https://vkrdownloader.xyz/server/?api_key=vkrdownloader&vkr={urllib.parse.quote(f'https://xhamster.com/videos/{slug}')}"
        response = requests.get(api_url)
        data = response.json().get('data', {})
        
        qualities = sorted(
            [q for q in data.get('downloads', []) if q.get('url', '').endswith('.mp4')],
            key=lambda x: int(re.search(r'(\d+)p', x.get('format_id', '0p')).group(1)),
            reverse=True
        )
        
        return qualities, data.get('title', 'xHamster Video'), data.get('thumbnail', None)
    except Exception as e:
        print(f"Error fetching qualities: {e}")
        return None, None, None

def create_quality_keyboard(request_id):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    request = video_requests.get(request_id)
    
    if not request:
        return None
    
    buttons = []
    for i, quality in enumerate(request.qualities[:4]):  # Limit to 4 qualities max
        btn_data = f"vid_{request_id}_{i}"
        buttons.append(
            types.InlineKeyboardButton(
                text=quality['format_id'],
                callback_data=btn_data
            )
        )
    
    # Add buttons in pairs
    for i in range(0, len(buttons), 2):
        keyboard.add(*buttons[i:i+2])
    
    return keyboard

@bot.message_handler(func=lambda m: 'xhamster.com/videos/' in m.text)
def handle_video_request(message):
    try:
        # Clean old requests
        for req_id in list(video_requests.keys()):
            if video_requests[req_id].is_expired():
                del video_requests[req_id]
        
        qualities, title, thumbnail = get_video_qualities(message.text)
        if not qualities:
            return bot.reply_to(message, "❌ Couldn't fetch video information")
        
        # Create new request entry
        request_id = hashlib.md5(f"{message.chat.id}{message.message_id}{datetime.now().timestamp()}".encode()).hexdigest()
        video_requests[request_id] = VideoRequest(qualities, title)
        
        # Create response
        keyboard = create_quality_keyboard(request_id)
        if not keyboard:
            return bot.reply_to(message, "❌ Error creating quality options")
        
        caption = f"🎬 {title}\nSelect quality:"
        
        if thumbnail:
            bot.send_photo(
                message.chat.id,
                thumbnail,
                caption=caption,
                reply_markup=keyboard
            )
        else:
            bot.send_message(
                message.chat.id,
                caption,
                reply_markup=keyboard
            )
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('vid_'))
def handle_quality_selection(call):
    try:
        _, request_id, quality_idx = call.data.split('_')
        request = video_requests.get(request_id)
        
        if not request or request.is_expired():
            return bot.answer_callback_query(call.id, "❌ Request expired. Please send the URL again.")
        
        quality_idx = int(quality_idx)
        if quality_idx >= len(request.qualities):
            return bot.answer_callback_query(call.id, "❌ Invalid quality selection")
        
        selected = request.qualities[quality_idx]
        bot.answer_callback_query(call.id, f"⬇️ Downloading {selected['format_id']}...")
        
        # Edit message to show download status
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⏳ Downloading {selected['format_id']} quality..."
        )
        
        # Start download in background
        download_video(call.message.chat.id, selected['url'])
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)}")

def download_video(chat_id, url):
    try:
        # Implement your download logic here
        # For example, using youtube-dl or requests
        # Then send the file using bot.send_video()
        
        # This is a placeholder - implement actual download
        bot.send_message(chat_id, f"📥 Download started from:\n{url}")
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Download failed: {str(e)}")

if __name__ == '__main__':
    print("Bot started...")
    bot.infinity_polling()
