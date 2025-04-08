from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

TOKEN = "8180063318:AAG2FtpVESnPYKuEszDIaewy-LXgVXXDS-o"

# Hardcoded sticker file_ids (replace with actual ones)
sticker_file_ids = [
    "CAACAgIAAxkBAAEL...1",
    "CAACAgIAAxkBAAEL...2",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sending all stickers...")
    for sticker_id in sticker_file_ids:
        try:
            await update.message.reply_sticker(sticker_id)
            await asyncio.sleep(0.5)  # Avoid flood limits
        except Exception as e:
            print(f"Error sending sticker: {e}")

async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    await application.run_polling()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
