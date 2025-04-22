import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter
import requests

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class LightweightGhibliFilter:
    @staticmethod
    def apply_filter(image_bytes: bytes) -> BytesIO:
        """Apply lightweight Ghibli-style filters to image"""
        try:
            # Open image
            img = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize for consistent processing
            img = img.resize((512, 512))
            
            # Apply Ghibli-style effects
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.3)  # Boost colors
            
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(0.9)  # Soften contrast
            
            # Add slight blur for painted effect
            img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
            
            # Save to bytes
            output = BytesIO()
            img.save(output, format='JPEG', quality=90)
            output.seek(0)
            
            return output
            
        except Exception as e:
            logger.error(f"Filter error: {e}")
            raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    await update.message.reply_text(
        "🎨 Lightweight Ghibli Filter Bot\n\n"
        "Send me a photo to apply a Ghibli-style filter!\n"
        "Note: This uses lightweight processing (not AI)"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process incoming photos"""
    try:
        # Send processing message
        processing_msg = await update.message.reply_text("Applying Ghibli filter...")
        
        # Get the photo file
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # Apply filter
        filtered_image = LightweightGhibliFilter.apply_filter(image_bytes)
        
        # Send result
        await update.message.reply_photo(
            photo=InputFile(filtered_image, filename="ghibli_style.jpg"),
            caption="Here's your Ghibli-style image!"
        )
        
        # Delete processing message
        await processing_msg.delete()
        
    except Exception as e:
        logger.error(f"Photo handling error: {e}")
        await update.message.reply_text("Failed to process image. Please try another photo.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error("Exception:", exc_info=context.error)
    if update.message:
        await update.message.reply_text("An error occurred. Please try again.")

def main():
    """Start the bot"""
    application = Application.builder().token("7414054511:AAG7IK7fyQfiApzxnF3rP7ZHJoWi_elWd3I").build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_error_handler(error_handler)
    
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
