from telegram import Update, InputSticker
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# Replace with your bot token
TOKEN = "8180063318:AAG2FtpVESnPYKuEszDIaewy-LXgVXXDS-o"

# List to store sticker file IDs (you can fetch these once and hardcode them)
sticker_file_ids = [
    "CAACAgIAAxkBAAEL...1",  # Replace with actual file_id
    "CAACAgIAAxkBAAEL...2",
    # Add all sticker file_ids from the pack
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"Hello {user.first_name}! Sending all stickers...")

    # Send all stickers one by one
    for sticker_id in sticker_file_ids:
        try:
            await update.message.reply_sticker(sticker_id)
            await asyncio.sleep(1)  # Avoid rate limits
        except Exception as e:
            print(f"Failed to send sticker: {e}")

async def main():
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add the /start command handler
    application.add_handler(CommandHandler("start", start))

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
