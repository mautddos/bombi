from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

TOKEN = "7554221154:AAF6slUuJGJ7tXuIDhEZP8LIOB5trSTz0gU"  # Replace with your actual token
STICKER_SET_NAME = "celebsex"  # From the URL https://t.me/addstickers/celebsex

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get the sticker set
        sticker_set = await context.bot.get_sticker_set(STICKER_SET_NAME)
        
        # Send all stickers with delay to avoid flooding
        await update.message.reply_text(f"Sending {len(sticker_set.stickers)} stickers...")
        
        for sticker in sticker_set.stickers:
            try:
                await update.message.reply_sticker(sticker.file_id)
                await asyncio.sleep(0.5)  # Important delay to avoid rate limits
            except Exception as e:
                print(f"Error sending sticker: {e}")
                continue
                
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == "__main__":
    main()
