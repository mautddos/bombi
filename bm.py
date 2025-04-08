from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

TOKEN = "7554221154:AAF6slUuJGJ7tXuIDhEZP8LIOB5trSTz0gU"

# Replace these with actual sticker file_ids from your pack
sticker_file_ids = [
    "CAACAgIAAxkBAAEL...1",
    "CAACAgIAAxkBAAEL...2",
    # Add all your sticker file_ids here
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sending all stickers...")
    for sticker_id in sticker_file_ids:
        try:
            await update.message.reply_sticker(sticker_id)
            await asyncio.sleep(0.3)  # Small delay to avoid flooding
        except Exception as e:
            print(f"Error sending sticker: {e}")

def main():
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add command handler
    application.add_handler(CommandHandler("start", start))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()  # Note: No asyncio.run() here!
