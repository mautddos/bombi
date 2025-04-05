import requests
import os
from datetime import datetime

# Configuration
BOT_TOKEN = "7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI"
CHAT_ID = "8167507955"
MP4_URL = "https://ip296322752.ahcdn.com/key=wSrpeebvepWT31ajWVtqGg,s=,end=1743836400,limit=3/data=43.153.85.245-dvp/state=Z-CmJAFJAHQjlBaoH-Ma/reftag=0201380214/ssd6/21/9/286482739/022/300/131/720p.h264.mp4"
MAX_SIZE = 45 * 1024 * 1024  # 45MB (under Telegram's 50MB limit)
CHUNK_SIZE = 1024 * 1024  # 1MB chunks

def download_video(url, filename):
    """Download video with progress tracking"""
    try:
        with requests.get(url, stream=True, timeout=3600) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            with open(filename, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        print(f"Downloaded {downloaded/1024/1024:.1f}MB", end='\r')
        print("\nDownload complete")
        return True
    except Exception as e:
        print(f"\nDownload failed: {str(e)}")
        return False

def split_video(input_file, chunk_size):
    """Split large video into chunks"""
    chunks = []
    try:
        file_size = os.path.getsize(input_file)
        part_num = 1
        
        with open(input_file, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                part_name = f"{input_file}.part{part_num}"
                with open(part_name, 'wb') as p:
                    p.write(chunk)
                chunks.append(part_name)
                part_num += 1
                
        print(f"Split into {len(chunks)} parts")
        return chunks
    except Exception as e:
        print(f"Splitting failed: {str(e)}")
        return []

def send_to_telegram(file_path, part_num=None):
    """Send file to Telegram with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            caption = "Full video download"
            if part_num:
                caption = f"Part {part_num} of video"
            
            with open(file_path, 'rb') as f:
                response = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                    data={
                        'chat_id': CHAT_ID,
                        'caption': caption,
                        'supports_streaming': 'false'
                    },
                    files={'video': f},
                    timeout=300
                )
            
            result = response.json()
            if result.get('ok'):
                print(f"✅ Part {part_num} sent successfully!")
                return True
            else:
                print(f"Attempt {attempt+1} failed: {result.get('description')}")
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
        
        if attempt < max_retries - 1:
            print("Waiting 10 seconds before retry...")
            time.sleep(10)
    
    return False

def main():
    temp_file = "full_video.mp4"
    
    # 1. Download the video
    if not download_video(MP4_URL, temp_file):
        return
    
    file_size = os.path.getsize(temp_file)
    print(f"Video size: {file_size/1024/1024:.1f}MB")
    
    # 2. Check if splitting is needed
    if file_size <= MAX_SIZE:
        # Send directly if small enough
        send_to_telegram(temp_file)
    else:
        # Split and send parts
        parts = split_video(temp_file, MAX_SIZE)
        for i, part in enumerate(parts, 1):
            if not send_to_telegram(part, i):
                print(f"Failed to send part {i}")
            # Clean up part
            os.remove(part)
    
    # Clean up
    if os.path.exists(temp_file):
        os.remove(temp_file)

if __name__ == "__main__":
    main()
