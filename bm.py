import logging
import os
import asyncio
import tempfile
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient
from bson.objectid import ObjectId

# Configuration
TOKEN = "7822455054:AAF-C_XdQBIAAWEXYDqQ2lrsIf1ewmDa46s"
MONGO_URI = "mongodb+srv://zqffpg:1HKKatlqTOBcOwa6@cluster0.7dwrm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
HLS_URL = "https://video-cf.xhcdn.com/8yE%2BseHYuE%2B6V0skGFlDrvM8w2V1Xg3Wy4L98rG6%2Bs0%3D/56/1744113600/media=hls4/multi=256x144:144p,426x240:240p/017/235/029/240p.h264.mp4.m3u8"
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB Telegram limit

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
    """Send a welcome message when the command /start is issued."""
    await update.message.reply_text('Hi! I am SEMXI VIDEO DOWNLOADER. Send me any message to get the video.')

async def download_original_video(input_url: str, output_path: str):
    """Download the original video without re-encoding."""
    command = [
        'ffmpeg',
        '-i', input_url,
        '-c', 'copy',  # No re-encoding to preserve quality
        '-f', 'mp4',
        output_path
    ]
    subprocess.run(command, check=True)

async def create_streamable_version(input_path: str, output_path: str):
    """Create a streamable version of the video."""
    command = [
        'ffmpeg',
        '-i', input_path,
        '-c:v', 'libx264', '-preset', 'fast',
        '-crf', '23',  # Balanced quality/size
        '-movflags', '+faststart',  # Enable streaming
        '-f', 'mp4',
        output_path
    ]
    subprocess.run(command, check=True)

async def send_video_package(update: Update, original_path: str, streamable_path: str):
    """Send both original and streamable versions to the user."""
    # Send original as document (no size limit)
    try:
        with open(original_path, 'rb') as original_file:
            await update.message.reply_document(
                document=original_file,
                caption="Original quality video (as document)"
            )
    except Exception as e:
        logger.error(f"Error sending original: {e}")
        raise

    # Check if streamable version exists and is under size limit
    if os.path.exists(streamable_path):
        streamable_size = os.path.getsize(streamable_path)
        if streamable_size < MAX_VIDEO_SIZE:
            try:
                with open(streamable_path, 'rb') as streamable_file:
                    await update.message.reply_video(
                        video=streamable_file,
                        caption="Streamable version",
                        supports_streaming=True
                    )
            except Exception as e:
                logger.error(f"Error sending streamable version: {e}")
                await update.message.reply_text(
                    "⚠️ Couldn't send streamable version, but original was sent successfully."
                )
        else:
            await update.message.reply_text(
                "ℹ️ Streamable version exceeds 50MB limit\n"
                "Download the original document for full quality"
            )

async def track_progress(update: Update, request_id: ObjectId, message: str):
    """Update user on progress and log to MongoDB."""
    await update.message.reply_text(message)
    requests_collection.update_one(
        {'_id': request_id},
        {'$set': {'progress': message}}
    )

async def cleanup_files(*files):
    """Clean up temporary files."""
    for file_path in files:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error cleaning up file {file_path}: {e}")

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main function to handle video processing and sending."""
    original_path = None
    streamable_path = None
    temp_dir = None
    
    try:
        # Create request record
        request_id = requests_collection.insert_one({
            'user_id': update.message.from_user.id,
            'status': 'processing',
            'progress': 'starting'
        }).inserted_id

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        original_path = os.path.join(temp_dir, "original.mp4")
        streamable_path = os.path.join(temp_dir, "streamable.mp4")

        # Step 1: Download original
        await track_progress(update, request_id, "⬇️ Downloading original video...")
        await download_original_video(HLS_URL, original_path)

        # Step 2: Create streamable version
        await track_progress(update, request_id, "🔄 Creating streamable version...")
        await create_streamable_version(original_path, streamable_path)

        # Step 3: Send both versions
        await track_progress(update, request_id, "📤 Sending video package...")
        await send_video_package(update, original_path, streamable_path)

        # Update status
        requests_collection.update_one(
            {'_id': request_id},
            {'$set': {'status': 'completed'}}
        )

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg processing error: {e}")
        await update.message.reply_text("❌ Video processing failed. Please try again.")
        requests_collection.update_one(
            {'_id': request_id},
            {'$set': {'status': 'failed', 'error': str(e)}}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await update.message.reply_text("❌ Something went wrong. Please try again later.")
        requests_collection.update_one(
            {'_id': request_id},
            {'$set': {'status': 'failed', 'error': str(e)}}
        )
    finally:
        # Clean up files
        if temp_dir:
            await cleanup_files(original_path, streamable_path)
            try:
                os.rmdir(temp_dir)
            except Exception as e:
                logger.error(f"Error removing temp directory: {e}")

def main():
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_video))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
