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
API_ID = 22625636  # Replace with your Telegram API ID
API_HASH = "f71778a6e1e102f33ccc4aee3b5cc697"  # Replace with your Telegram API hash
MONGO_URI = "mongodb+srv://zqffpg:1HKKatlqTOBcOwa6@cluster0.7dwrm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
HLS_URL = "https://video-cf.xhcdn.com/8yE%2BseHYuE%2B6V0skGFlDrvM8w2V1Xg3Wy4L98rG6%2Bs0%3D/56/1744113600/media=hls4/multi=256x144:144p,426x240:240p/017/235/029/240p.h264.mp4.m3u8"
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB Telegram limit
MAX_CHUNK_SIZE = 45 * 1024 * 1024  # 45MB to be safe (leaving room for metadata)

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

async def convert_video(input_url: str, output_path: str):
    """Convert HLS to MP4 with optimized settings for size"""
    command = [
        'ffmpeg',
        '-i', input_url,
        '-c:v', 'libx264', '-preset', 'fast',
        '-crf', '28',  # Higher CRF for smaller files (23-28 is reasonable)
        '-movflags', '+faststart',
        '-vf', 'scale=640:-2',  # Resize to 640 width
        '-c:a', 'aac', '-b:a', '128k',  # Audio settings
        '-f', 'mp4',
        output_path
    ]
    subprocess.run(command, check=True)

async def split_video_by_size(input_path: str, output_dir: str):
    """Split video into chunks based on size (not duration)"""
    # Get video duration in seconds
    probe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ]
    duration = float(subprocess.check_output(probe_cmd).decode('utf-8').strip())
    
    # Get file size
    file_size = os.path.getsize(input_path)
    num_chunks = max(1, (file_size + MAX_CHUNK_SIZE - 1) // MAX_CHUNK_SIZE
    
    # Calculate split points
    split_points = [i * (duration / num_chunks) for i in range(1, num_chunks)]
    
    # Create split command
    output_template = os.path.join(output_dir, 'part_%03d.mp4')
    command = [
        'ffmpeg',
        '-i', input_path,
        '-c', 'copy',
        '-f', 'segment',
        '-segment_times', ','.join(map(str, split_points)),
        '-reset_timestamps', '1',
        output_template
    ]
    subprocess.run(command, check=True)
    
    return sorted([f for f in os.listdir(output_dir) if f.startswith('part_')])

async def send_video_chunks(update: Update, chunks: list, chunk_dir: str):
    """Send video chunks to user with progress updates"""
    total_parts = len(chunks)
    for i, chunk in enumerate(chunks, 1):
        chunk_path = os.path.join(chunk_dir, chunk)
        chunk_size = os.path.getsize(chunk_path) / (1024 * 1024)  # in MB
        
        try:
            with open(chunk_path, 'rb') as f:
                await update.message.reply_text(f"📤 Uploading part {i}/{total_parts} ({chunk_size:.1f}MB)...")
                await update.message.reply_video(
                    video=f,
                    caption=f"Part {i} of {total_parts}",
                    supports_streaming=True,
                    read_timeout=60,
                    write_timeout=60,
                    connect_timeout=60
                )
            os.remove(chunk_path)
        except Exception as e:
            logger.error(f"Error sending chunk {i}: {e}")
            await update.message.reply_text(f"⚠️ Failed to send part {i}. Please try again.")
            raise

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Create request record
        request_id = requests_collection.insert_one({
            'user_id': update.message.from_user.id,
            'status': 'processing',
            'progress': 0
        }).inserted_id

        await update.message.reply_text("⏳ Processing your video, please wait...")
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Step 1: Convert HLS to MP4 with size optimization
            output_file = os.path.join(tmp_dir, "output.mp4")
            await convert_video(HLS_URL, output_file)
            
            # Step 2: Check size and split if needed
            file_size = os.path.getsize(output_file)
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size > MAX_VIDEO_SIZE:
                await update.message.reply_text(
                    f"📦 Video size is {file_size_mb:.1f}MB (over {MAX_VIDEO_SIZE/(1024*1024)}MB limit). "
                    "Splitting into parts..."
                )
                chunk_dir = os.path.join(tmp_dir, "chunks")
                os.makedirs(chunk_dir, exist_ok=True)
                chunks = await split_video_by_size(output_file, chunk_dir)
                await send_video_chunks(update, chunks, chunk_dir)
            else:
                await update.message.reply_text(f"📤 Uploading {file_size_mb:.1f}MB video...")
                with open(output_file, 'rb') as f:
                    await update.message.reply_video(
                        video=f,
                        caption="Here's your video!",
                        supports_streaming=True,
                        read_timeout=60,
                        write_timeout=60,
                        connect_timeout=60
                    )
            
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
            requests_collection.update_one(
                {'_id': request_id},
                {'$set': {'status': 'failed' if 'e' in locals() else 'completed'}}
            )

def main():
    # Create application with API credentials
    application = Application.builder() \
        .token(TOKEN) \
        .base_url("https://api.telegram.org") \  # You can use a custom URL if needed
        .base_file_url("https://api.telegram.org/file") \
        .build()
        
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_video))
    
    # Run with more aggressive timeout settings
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        read_timeout=60,
        write_timeout=60,
        connect_timeout=60,
        pool_timeout=60
    )

if __name__ == '__main__':
    main()
