import requests
import os
from urllib.parse import urlparse

# Configuration
BOT_TOKEN = "7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI"
CHAT_ID = "8167507955"
MP4_URL = "https://ip296322752.ahcdn.com/key=wSrpeebvepWT31ajWVtqGg,s=,end=1743836400,limit=3/data=43.153.85.245-dvp/state=Z-CmJAFJAHQjlBaoH-Ma/reftag=0201380214/ssd6/21/9/286482739/022/300/131/720p.h264.mp4"
OUTPUT_FILE = "downloaded_video.mp4"
CHUNK_SIZE = 1024 * 1024  # 1MB chunks

def download_video(url, filename):
    """Download video with progress tracking"""
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            with open(filename, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:  # filter out keep-alive chunks
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"Downloaded {downloaded/1024/1024:.1f}MB ({percent:.1f}%)", end='\r')
                        else:
                            print(f"Downloaded {downloaded/1024/1024:.1f}MB", end='\r')
            print("\nDownload completed successfully!")
            return True
            
    except Exception as e:
        print(f"\nDownload failed: {str(e)}")
        return False

def send_video_to_telegram(file_path):
    """Send video to Telegram ensuring full download"""
    try:
        file_size = os.path.getsize(file_path)
        print(f"Uploading {file_size/1024/1024:.1f}MB video...")
        
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                data={
                    'chat_id': CHAT_ID,
                    'supports_streaming': 'false'  # Force full download
                },
                files={'video': f},
                timeout=300  # 5 minute timeout
            )
        
        result = response.json()
        if result.get('ok'):
            print("✅ Video successfully sent to Telegram!")
            return True
        else:
            print("❌ Failed to send video:", result.get('description', 'Unknown error'))
            return False
            
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        return False

def main():
    # Step 1: Download the MP4 video
    if not download_video(MP4_URL, OUTPUT_FILE):
        return
    
    # Step 2: Send to Telegram
    if not send_video_to_telegram(OUTPUT_FILE):
        return
    
    # Clean up
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        print("Temporary file removed")

if __name__ == "__main__":
    main()
