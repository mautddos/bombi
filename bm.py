import logging
import os
import asyncio
import tempfile
import subprocess
import math
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient
from bson.objectid import ObjectId

# Configuration
TOKEN = "7822455054:AAF-C_XdQBIAAWEXYDqQ2lrsIf1ewmDa46s"
MONGO_URI = "mongodb+srv://zqffpg:1HKKatlqTOBcOwa6@cluster0.7dwrm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
HLS_URL = "your_hls_url"
MAX_DOCUMENT_SIZE = 2000 * 1024 * 1024  # 2GB Telegram document limit
CHUNK_SIZE = 45 * 1024 * 1024  # 45MB chunks (under 50MB limit)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client.video_bot
requests_collection = db.requests

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hi! I am SEMXI VIDEO DOWNLOADER. Send me any message to get the video.')

async def download_video(input_url: str, output_path: str):
    """Download video with progress tracking"""
    command = [
        'ffmpeg',
        '-i', input_url,
        '-c', 'copy',
        '-f', 'mp4',
        output_path
    ]
    subprocess.run(command, check=True)

async def split_large_file(file_path: str, chunk_size: int):
    """Split large file into chunks"""
    chunk_dir = tempfile.mkdtemp()
    base_name = os.path.basename(file_path)
    chunk_pattern = os.path.join(chunk_dir, f"part_%03d_{base_name}")
    
    command = [
        'split',
        '--bytes=' + str(chunk_size),
        '--numeric-suffixes',
        '--suffix-length=3',
        file_path,
        chunk_pattern
    ]
    subprocess.run(command, check=True)
    
    chunks = sorted([
        os.path.join(chunk_dir, f) 
        for f in os.listdir(chunk_dir) 
        if f.startswith('part_')
    ])
    return chunks

async def send_large_document(update: Update, file_path: str):
    """Send large document in chunks if needed"""
    file_size = os.path.getsize(file_path)
    
    if file_size <= CHUNK_SIZE:
        # Send as single document if small enough
        with open(file_path, 'rb') as f:
            await update.message.reply_document(
                document=InputFile(f, filename=os.path.basename(file_path)),
                caption="Full video"
            )
    else:
        # Split and send chunks
        chunks = await split_large_file(file_path, CHUNK_SIZE)
        total_chunks = len(chunks)
        
        for i, chunk_path in enumerate(chunks, 1):
            with open(chunk_path, 'rb') as f:
                await update.message.reply_document(
                    document=InputFile(f, filename=f"part_{i:03d}_of_{total_chunks}"),
                    caption=f"Part {i} of {total_chunks}"
                )
            os.remove(chunk_path)
        
        # Clean up empty directory
        os.rmdir(os.path.dirname(chunks[0]))

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    temp_file = None
    try:
        # Create request record
        request_id = requests_collection.insert_one({
            'user_id': update.message.from_user.id,
            'status': 'processing'
        }).inserted_id

        await update.message.reply_text("⬇️ Downloading video...")
        
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            temp_file = tmp_file.name
        
        # Download original
        await download_video(HLS_URL, temp_file)
        
        # Check file size
        file_size = os.path.getsize(temp_file)
        await update.message.reply_text(f"📦 File size: {file_size/1024/1024:.2f}MB")
        
        if file_size > MAX_DOCUMENT_SIZE:
            await update.message.reply_text("❌ File too large (over 2GB). Cannot send.")
            return
        
        # Send as document
        await update.message.reply_text("📤 Uploading to Telegram...")
        await send_large_document(update, temp_file)
        
        # Update status
        requests_collection.update_one(
            {'_id': request_id},
            {'$set': {'status': 'completed', 'size': file_size}}
        )
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e}")
        await update.message.reply_text("❌ Video processing failed. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await update.message.reply_text("❌ Something went wrong. Please try again later.")
    finally:
        # Clean up
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
        if 'request_id' in locals():
            requests_collection.update_one(
                {'_id': request_id},
                {'$set': {'status': 'failed' if 'e' in locals() else 'completed'}}
            )

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_video))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
