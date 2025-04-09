import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from telethon import TelegramClient
from config import BOT_TOKEN, API_ID, API_HASH
import os

# Set up bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Userbot session (to bypass 50MB limit)
client = TelegramClient("session", API_ID, API_HASH)

# Start userbot
async def start_userbot():
    await client.start(bot_token=BOT_TOKEN)
    print("Userbot ready.")

@dp.message_handler(lambda message: message.text.startswith("http"))
async def handle_link(message: types.Message):
    url = message.text.strip()
    encoded = requests.utils.quote(url)
    api_url = f"https://vkrdownloader.xyz/server/?api_key=vkrdownloader&vkr={encoded}"

    try:
        res = requests.get(api_url).json()
        downloads = res["data"]["downloads"]
        thumb = res["data"]["thumbnail"]

        buttons = InlineKeyboardMarkup(row_width=2)
        for d in downloads:
            if d["url"].endswith(".mp4"):
                btn = InlineKeyboardButton(
                    text=f'{d["format_id"]} - {d["size"]}',
                    callback_data=d["url"]
                )
                buttons.add(btn)

        await bot.send_photo(
            chat_id=message.chat.id,
            photo=thumb,
            caption="⏬ *Choose resolution to download:*",
            reply_markup=buttons,
            parse_mode="Markdown"
        )

    except Exception as e:
        await message.answer(f"❌ Error: {e}")

@dp.callback_query_handler()
async def callback_video(call: types.CallbackQuery):
    await call.answer("⏳ Downloading your video, please wait...")
    try:
        url = call.data
        filename = "video.mp4"

        # Download video
        r = requests.get(url, stream=True)
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Send via userbot
        await client.send_file(call.message.chat.id, filename, caption="✅ Here's your video!")
        os.remove(filename)

    except Exception as e:
        await call.message.answer(f"❌ Failed to send video.\nError: `{e}`", parse_mode="Markdown")

async def main():
    await start_userbot()
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
