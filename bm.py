import logging
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import subprocess
import tempfile
from pymongo import MongoClient
from bson.objectid import ObjectId
import asyncio

# Configuration
TOKEN = "7822455054:AAF-C_XdQBIAAWEXYDqQ2lrsIf1ewmDa46s"
MONGO_URI = "mongodb+srv://zqffpg:1HKKatlqTOBcOwa6@cluster0.7dwrm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
HLS_URL = "https://video-cf.xhcdn.com/8yE%2BseHYuE%2B6V0skGFlDrvM8w2V1Xg3Wy4L98rG6%2Bs0%3D/56/1744113600/media=hls4/multi=256x144:144p,426x240:240p/017/235/029/240p.h264.mp4.m3u8"

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

async def track_progress(update: Update, file_path: str, request_id: ObjectId):
    """Track conversion progress and update user"""
    last_update = 0
    while True:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            requests_collection.update_one(
                {'_id': request_id},
                {'$set': {'progress': size}}
            )
            
            # Update user every 5MB progress
            if size - last_update > 5_000_000:
                mb = size / (1024 * 1024)
                await update.message.reply_text(f"🔄 Processing: {mb:.1f}MB downloaded")
                last_update = size
                
        await asyncio.sleep(5)

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Create request record in MongoDB
        request_id = requests_collection.insert_one({
            'user_id': update.message.from_user.id,
            'status': 'processing',
            'progress': 0
        }).inserted_id

        await update.message.reply_text("⏳ Starting video processing...")
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, "output.mp4")
            
            # Start progress tracking
            progress_task = asyncio.create_task(
                track_progress(update, output_file, request_id)
            
            # Convert using ffmpeg with optimized settings
            command = [
                'ffmpeg',
                '-i', HLS_URL,
                '-c:v', 'libx264', '-preset', 'fast',
                '-crf', '28',  # Better compression
                '-movflags', 'frag_keyframe+empty_moov',
                '-f', 'mp4',
                output_file
            ]
            
            # Run ffmpeg
            subprocess.run(command, check=True)
            
            # Stop progress tracking
            progress_task.cancel()
            
            # Send video in chunks if too large
            max_size = 50 * 1024 * 1024  # 50MB Telegram limit
            file_size = os.path.getsize(output_file)
            
            if file_size > max_size:
                await update.message.reply_text("📦 Video is large, sending in parts...")
                await send_large_video(update, output_file)
            else:
                with open(output_file, 'rb') as video_file:
                    await update.message.reply_video(video=video_file)
            
            requests_collection.update_one(
                {'_id': request_id},
                {'$set': {'status': 'completed'}}
            )
            
    except Exception as e:
        logger.error(f"Error: {e}")
        requests_collection.update_one(
            {'_id': request_id},
            {'$set': {'status': 'failed', 'error': str(e)}}
        )
        await update.message.reply_text("❌ Error processing video. Please try again later.")

async def send_large_video(update: Update, file_path: str):
    """Split and send large video in parts"""
    try:
        # Split video using ffmpeg
        split_dir = tempfile.mkdtemp()
        split_command = [
            'ffmpeg',
            '-i', file_path,
            '-c', 'copy',
            '-f', 'segment',
            '-segment_time', '300',  # 5 minute chunks
            '-reset_timestamps', '1',
            os.path.join(split_dir, 'part%03d.mp4')
        ]
        subprocess.run(split_command, check=True)
        
        # Send each part
        parts = sorted([f for f in os.listdir(split_dir) if f.startswith('part')])
        for part in parts:
            part_path = os.path.join(split_dir, part)
            with open(part_path, 'rb') as f:
                await update.message.reply_video(
                    video=f,
                    caption=f"Part {parts.index(part)+1} of {len(parts)}"
                )
            os.remove(part_path)
            
    except Exception as e:
        logger.error(f"Error sending large video: {e}")
        raise

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_video))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
