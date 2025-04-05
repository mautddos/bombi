import requests
import os
import time

# Configuration
BOT_TOKEN = "7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI"
CHAT_ID = "8167507955"
VIDEO_URL = "https://ip296321550.ahcdn.com/key=ZVah3Txj1tCBKt+HLrXfrQ,s=,end=1743840000/data=18.180.253.18-dvp/state=Z-CxJAFJAHQjlBaoH-Ma/reftag=0201380214/media=hls4/ssd6/21/1/132727041.mp4/index.m3u8"
MAX_RETRIES = 3
CHUNK_SIZE = 1024 * 1024  # 1MB chunks

def download_with_retry(url, filename):
    """Download file with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Download attempt {attempt + 1}/{MAX_RETRIES}")
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                
                with open(filename, 'wb') as f:
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:  # filter out keep-alive chunks
                            f.write(chunk)
                            downloaded += len(chunk)
                            print(f"Downloaded {downloaded/1024/1024:.1f}MB", end='\r')
                print("\nDownload completed successfully!")
                return True
        except Exception as e:
            print(f"\nDownload failed: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                print("Waiting 5 seconds before retry...")
                time.sleep(5)
    return False

def send_large_video(file_path):
    """Send large video to Telegram with progress tracking"""
    try:
        file_size = os.path.getsize(file_path)
        print(f"Preparing to upload {file_size/1024/1024:.1f}MB video...")
        
        with open(file_path, 'rb') as f:
            files = {'video': f}
            data = {
                'chat_id': CHAT_ID,
                'caption': 'Full video download',
                'supports_streaming': False  # Ensures full download
            }
            
            # Use a session for better performance
            with requests.Session() as session:
                response = session.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                    data=data,
                    files=files,
                    timeout=60
                )
                
        result = response.json()
        if result.get('ok'):
            print("Video successfully sent to Telegram!")
            return True
        else:
            print("Failed to send video:", result.get('description', 'Unknown error'))
            return False
            
    except Exception as e:
        print(f"Upload failed: {str(e)}")
        return False

def main():
    temp_file = "full_video.mp4"
    
    # Step 1: Download the video
    if not download_with_retry(VIDEO_URL, temp_file):
        print("Failed to download video after multiple attempts")
        return
    
    # Step 2: Send to Telegram
    if not send_large_video(temp_file):
        print("Failed to send video to Telegram")
    
    # Clean up
    if os.path.exists(temp_file):
        os.remove(temp_file)
        print("Temporary file removed")

if __name__ == "__main__":
    main()
