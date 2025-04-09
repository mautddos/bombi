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

async def convert_video(input_url: str, output_path: str):
    """Convert HLS to MP4 with optimized settings"""
    command = [
        'ffmpeg',
        '-i', input_url,
        '-c:v', 'libx264', '-preset', 'fast',
        '-crf', '23',  # Balanced quality/size
        '-movflags', '+faststart',
        '-vf', 'scale=640:-2',  # Resize to 640 width
        '-f', 'mp4',
        output_path
    ]
    subprocess.run(command, check=True)

async def split_video(input_path: str, output_dir: str, segment_time: int = 300):
    """Split video into smaller chunks"""
    command = [
        'ffmpeg',
        '-i', input_path,
        '-c', 'copy',
        '-f', 'segment',
        '-segment_time', str(segment_time),
        '-reset_timestamps', '1',
        os.path.join(output_dir, 'part_%03d.mp4')
    ]
    subprocess.run(command, check=True)
    return sorted([f for f in os.listdir(output_dir) if f.startswith('part_')])

async def send_video_chunks(update: Update, chunks: list, chunk_dir: str):
    """Send video chunks to user"""
    for i, chunk in enumerate(chunks, 1):
        chunk_path = os.path.join(chunk_dir, chunk)
        try:
            with open(chunk_path, 'rb') as f:
                await update.message.reply_video(
                    video=f,
                    caption=f"Part {i} of {len(chunks)}",
                    supports_streaming=True
                )
            os.remove(chunk_path)
        except Exception as e:
            logger.error(f"Error sending chunk {i}: {e}")
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
            # Step 1: Convert HLS to MP4
            output_file = os.path.join(tmp_dir, "output.mp4")
            await convert_video(HLS_URL, output_file)
            
            # Step 2: Check size and split if needed
            file_size = os.path.getsize(output_file)
            if file_size > MAX_VIDEO_SIZE:
                await update.message.reply_text("📦 Video is large, splitting into parts...")
                chunk_dir = tempfile.mkdtemp()
                chunks = await split_video(output_file, chunk_dir)
                await send_video_chunks(update, chunks, chunk_dir)
            else:
                with open(output_file, 'rb') as f:
                    await update.message.reply_video(
                        video=f,
                        caption="Here's your video!",
                        supports_streaming=True
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
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_video))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
