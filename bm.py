import logging
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

async def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.content

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Hi! I'm Ghibli Style Bot (API Version).\n"
        "Send me an image and I'll transform it using a cloud-based AI!"
    )

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the received image using Hugging Face API."""
    await update.message.reply_text("Processing your image via API...")
    
    try:
        # Get the photo file
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # Call the API
        output = await query({
            "inputs": {
                "image": image_bytes,
                "prompt": "Ghibli-style anime painting",
                "strength": 0.6
            }
        })
        
        # Send back the result
        await update.message.reply_photo(photo=InputFile(BytesIO(output)))
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("API processing failed. Please try again later.")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token("7414054511:AAG7IK7fyQfiApzxnF3rP7ZHJoWi_elWd3I").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, process_image))
    application.run_polling()

if __name__ == '__main__':
    main()
