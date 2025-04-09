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
    await update.message.reply_text('Hi! I am SEMXI VIDEO DOWNLOADER. Send me any message to get the video.')

async def download_original(input_url: str, output_path: str):
    """Download original video without re-encoding"""
    command = [
        'ffmpeg',
        '-i', input_url,
        '-c', 'copy',  # No re-encoding
        '-f', 'mp4',
        output_path
    ]
    subprocess.run(command, check=True)

async def create_streamable_version(input_path: str, output_path: str):
    """Create optimized version for streaming"""
    command = [
        'ffmpeg',
        '-i', input_path,
        '-c:v', 'libx264', '-preset', 'fast',
        '-crf', '23',
        '-movflags', '+faststart',
        '-vf', 'scale=640:-2',
        '-f', 'mp4',
        output_path
    ]
    subprocess.run(command, check=True)

async def send_video_package(update: Update, original_path: str, streamable_path: str):
    """Send both original and streamable versions"""
    # Send original as document (no size limit)
    with open(original_path, 'rb') as f:
        await update.message.reply_document(
            document=f,
            caption="Original quality (as document)"
        )
    
    # Send streamable version if under size limit
    streamable_size = os.path.getsize(streamable_path)
    if streamable_size < MAX_VIDEO_SIZE:
        with open(streamable_path, 'rb') as f:
            await update.message.reply_video(
                video=f,
                caption="Streamable version",
                supports_streaming=True
            )
    else:
        await update.message.reply_text(
            "ℹ️ Streamable version exceeds 50MB limit\n"
            "Download the original document for full quality"
        )

async def track_progress(update: Update, request_id: ObjectId, stage: str):
    """Update user on progress"""
    messages = {
        'downloading': "⬇️ Downloading original video...",
        'converting': "🔄 Creating streamable version...",
        'sending': "📤 Uploading to Telegram..."
    }
    await update.message.reply_text(messages[stage])
    requests_collection.update_one(
        {'_id': request_id},
        {'$set': {'stage': stage}}
    )

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Create request record
        request_id = requests_collection.insert_one({
            'user_id': update.message.from_user.id,
            'status': 'processing',
            'stage': 'starting'
        }).inserted_id

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Step 1: Download original
            original_path = os.path.join(tmp_dir, "original.mp4")
            await track_progress(update, request_id, 'downloading')
            await download_original(HLS_URL, original_path)
            
            # Step 2: Create streamable version
            streamable_path = os.path.join(tmp_dir, "streamable.mp4")
            await track_progress(update, request_id, 'converting')
            await create_streamable_version(original_path, streamable_path)
            
            # Step 3: Send both versions
            await track_progress(update, request_id, 'sending')
            await send_video_package(update, original_path, streamable_path)
            
            # Update status
            requests_collection.update_one(
                {'_id': request_id},
                {'$set': {'status': 'completed'}}
            )
            
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e}")
        await update.message.reply_text("❌ Video processing failed. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await update.message.reply_text("❌ Something went wrong. Please try again later.")
    finally:
        if 'request_id' in locals():
            status = 'failed' if 'e' in locals() else 'completed'
            requests_collection.update_one(
                {'_id': request_id},
                {'$set': {'status': status}}
            )

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_video))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
