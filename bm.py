import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import numpy as np

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class GhibliConverter:
    @staticmethod
    def apply_ghibli_style(image_bytes: bytes) -> BytesIO:
        """Apply authentic Ghibli-style transformation"""
        try:
            # Open and convert image
            img = Image.open(BytesIO(image_bytes)).convert('RGB')
            
            # Resize maintaining aspect ratio
            img = ImageOps.fit(img, (512, 512), method=Image.LANCZOS)
            
            # Convert to numpy array for processing
            arr = np.array(img).astype('float32') / 255.0
            
            # Ghibli-style color transformation (subtle, artistic adjustment)
            arr[:,:,0] = arr[:,:,0] * 0.9  # Reduce red slightly
            arr[:,:,1] = arr[:,:,1] * 1.2  # Increase green (for vibrancy)
            arr[:,:,2] = arr[:,:,2] * 1.05  # Boost blue moderately

            # Enhance the vibrancy of the image by adjusting saturation and contrast
            arr = np.clip(arr * 1.1, 0, 1)  # Overall vibrance boost
            
            # Apply soft light effect using Gaussian Blur
            blur = Image.fromarray((arr * 255).astype('uint8')).filter(
                ImageFilter.GaussianBlur(radius=5))  # Increase blur radius for soft glow
            arr = np.minimum(arr * 1.15, np.array(blur) / 255.0 * 1.2)  # Soft light glow effect

            # Convert back to PIL Image
            result = Image.fromarray((arr * 255).astype('uint8'))
            
            # Increase sharpness and contrast for more artistic detail
            enhancer = ImageEnhance.Sharpness(result)
            result = enhancer.enhance(1.5)  # Increased sharpness for finer details
            
            # Further enhancement to increase contrast
            enhancer_contrast = ImageEnhance.Contrast(result)
            result = enhancer_contrast.enhance(1.3)  # Enhance contrast for a more striking effect

            # Save to bytes
            output = BytesIO()
            result.save(output, format='JPEG', quality=95, optimize=True)
            output.seek(0)
            
            return output
            
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    await update.message.reply_text(
        "🎨 Studio Ghibli Style Bot\n\n"
        "Send me any photo to transform it into authentic Ghibli-style artwork!\n\n"
        "Tips:\n"
        "- Use well-lit photos for best results\n"
        "- Portraits and landscapes work great\n"
        "- Processing takes just a few seconds"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process incoming photos"""
    try:
        # Send processing message
        msg = await update.message.reply_text("🖌️ Painting your Ghibli masterpiece...")
        
        # Get highest quality photo
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # Apply transformation
        result = GhibliConverter.apply_ghibli_style(image_bytes)
        
        # Send result
        await update.message.reply_photo(
            photo=InputFile(result, filename="ghibli_art.jpg"),
            caption="✨ Your Ghibli-style artwork is ready!"
        )
        
        # Clean up
        await msg.delete()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "❌ Couldn't process that image. Please try another photo."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error("Exception:", exc_info=context.error)
    if update.message:
        await update.message.reply_text("⚠️ An error occurred. Please try again.")

def main():
    """Start the bot"""
    application = Application.builder().token("7414054511:AAG7IK7fyQfiApzxnF3rP7ZHJoWi_elWd3I").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_error_handler(error_handler)
    
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
