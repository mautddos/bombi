import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "7554221154:AAF6slUuJGJ7tXuIDhEZP8LIOB5trSTz0gU"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to the Direct Video Downloader Bot!\n\n"
        "Send me a video URL and I'll send it back to you directly."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()
    
    try:
        await update.message.reply_text("⏳ Fetching video...")
        
        # Check if the URL is accessible
        response = requests.head(url, timeout=10)
        if response.status_code != 200:
            raise Exception("URL not accessible")
        
        # Check content type to ensure it's a video
        content_type = response.headers.get('content-type', '')
        if 'video' not in content_type.lower():
            raise Exception("URL doesn't point to a direct video file")
        
        # Send the video directly
        await update.message.reply_video(
            video=url,
            caption="Here's your video!",
            supports_streaming=True
        )
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
        print(f"Error processing {url}: {str(e)}")

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
