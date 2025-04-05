import requests
import os
import subprocess
from datetime import datetime

# Configuration
BOT_TOKEN = "7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI"
CHAT_ID = "8167507955"
VIDEO_URL = "https://ip296322752.ahcdn.com/key=wSrpeebvepWT31ajWVtqGg,s=,end=1743836400,limit=3/data=43.153.85.245-dvp/state=Z-CmJAFJAHQjlBaoH-Ma/reftag=0201380214/ssd6/21/9/286482739/022/300/131/720p.h264.mp4"
MAX_SIZE = 45 * 1024 * 1024  # 45MB chunks
TIMEOUT = 300  # 5 minutes

def check_video_integrity(file_path):
    """Verify video is playable using ffprobe"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def convert_video(input_path, output_path):
    """Convert to Telegram-friendly format"""
    try:
        subprocess.run([
            "ffmpeg", "-i", input_path,
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",
            "-f", "mp4", output_path,
            "-y"
        ], check=True)
        return True
    except:
        return False

def download_file(url, filename):
    """Download with integrity checks"""
    try:
        with requests.get(url, stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        if not check_video_integrity(filename):
            print("Downloaded file is corrupted, retrying...")
            os.remove(filename)
            return False
            
        return True
    except Exception as e:
        print(f"Download failed: {str(e)}")
        return False

def send_video_part(file_path, part_num=None):
    """Send with enhanced validation"""
    try:
        caption = "Full video" if not part_num else f"Part {part_num}"
        
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                files={'video': f},
                data={
                    'chat_id': CHAT_ID,
                    'caption': caption,
                    'supports_streaming': 'false'
                },
                timeout=TIMEOUT
            )
        
        return response.json().get('ok', False)
    except:
        return False

def main():
    temp_files = []
    
    try:
        # 1. Download original
        original_file = "original_vid.mp4"
        if not download_file(VIDEO_URL, original_file):
            return
        temp_files.append(original_file)
        
        # 2. Convert if needed
        final_file = "converted_vid.mp4"
        if not check_video_integrity(original_file) or os.path.getsize(original_file) > MAX_SIZE:
            if not convert_video(original_file, final_file):
                return
            temp_files.append(final_file)
        else:
            final_file = original_file
        
        # 3. Send in parts if large
        file_size = os.path.getsize(final_file)
        if file_size <= MAX_SIZE:
            if not send_video_part(final_file):
                print("Failed to send complete video")
        else:
            # Split and send logic would go here
            print("Video too large - implement splitting here")
            
    finally:
        # Cleanup
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    main()
