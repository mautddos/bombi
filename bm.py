import logging
import base64
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
import requests
from PIL import Image

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

API_URL = "https://api-inference.huggingface.co/models/nitrosocke/Ghibli-Diffusion"
API_TOKEN = "YOUR_HUGGINGFACE_API_TOKEN"

headers = {"Authorization": f"Bearer {API_TOKEN}"}

async def query(image_bytes):
    """Send image to Hugging Face API"""
    try:
        # Convert image to base64
        image = Image.open(BytesIO(image_bytes))
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        payload = {
            "inputs": {
                "image": img_str,
                "prompt": "Ghibli-style anime painting, soft pastel colors, highly detailed",
                "strength": 0.6
            }
        }
        
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
        
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message"""
    await update.message.reply_text(
        "🎨 Hi! I'm Ghibli Style Bot\n"
        "Send me a photo to transform it into Studio Ghibli-style artwork!\n\n"
        "Note: Processing takes about 10-20 seconds"
    )

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photos"""
    try:
        message = await update.message.reply_text("🔄 Processing your image...")
        
        # Get highest resolution photo
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # Call API
        result_bytes = await query(image_bytes)
        
        # Send result
        await update.message.reply_photo(
            photo=InputFile(BytesIO(result_bytes), 
            caption="Here's your Ghibli-style artwork! ✨"
        )
        
        # Delete processing message
        await message.delete()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API Request failed: {e}")
        await update.message.reply_text("🚨 The AI service is currently unavailable. Please try again later.")
    except Exception as e:
        logger.error(f"Processing error: {e}")
        await update.message.reply_text("❌ Sorry, I couldn't process that image. Please try with a different photo.")

def main() -> None:
    """Start the bot"""
    application = Application.builder().token("7414054511:AAG7IK7fyQfiApzxnF3rP7ZHJoWi_elWd3I").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, process_image))
    
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
