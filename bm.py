import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline
import torch

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variable for the pipeline
pipe = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.first_name}! I'm Ghibli Style Bot.\n"
        "Send me an image and I'll transform it into a Ghibli-style artwork!\n\n"
        "Just send me any photo and wait for the magic to happen."
    )

async def load_model() -> None:
    """Load the Stable Diffusion model."""
    global pipe
    if pipe is None:
        logger.info("Loading model...")
        model_id = "nitrosocke/Ghibli-Diffusion"
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            model_id,
            torch_dtype=dtype
        )
        pipe.to("cuda" if torch.cuda.is_available() else "cpu")
        pipe.enable_attention_slicing()
        logger.info("Model loaded!")

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the received image."""
    await update.message.reply_text("Processing your image... Please wait, this may take a while.")
    
    try:
        # Get the photo file
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = BytesIO(await photo_file.download_as_bytearray())
        
        # Open and prepare the image
        image = Image.open(photo_bytes).convert("RGB")
        image = image.resize((512, 512))
        
        # Generate the Ghibli-style image
        prompt = "Ghibli-style anime painting, soft pastel colors, highly detailed, masterpiece"
        strength = 0.6  # You can make this configurable
        
        result = pipe(
            prompt=prompt,
            image=image,
            strength=strength
        ).images[0]
        
        # Send the result back
        bio = BytesIO()
        bio.name = 'ghibli_result.jpg'
        result.save(bio, 'JPEG')
        bio.seek(0)
        
        await update.message.reply_photo(photo=InputFile(bio), caption="Here's your Ghibli-style artwork!")
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("Sorry, something went wrong while processing your image. Please try again.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update.message:
        await update.message.reply_text("An error occurred while processing your request. Please try again.")

def main() -> None:
    """Start the bot."""
    # Load the model first
    import asyncio
    asyncio.run(load_model())
    
    # Create the Application
    application = Application.builder().token("7414054511:AAG7IK7fyQfiApzxnF3rP7ZHJoWi_elWd3I").build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, process_image))
    application.add_error_handler(error_handler)
    
    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
