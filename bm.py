import requests
import os
import sys

# Configuration
BOT_TOKEN = "7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI"
CHAT_ID = "8167507955"
VIDEO_URL = "https://ip296321550.ahcdn.com/key=ZVah3Txj1tCBKt+HLrXfrQ,s=,end=1743840000/data=18.180.253.18-dvp/state=Z-CxJAFJAHQjlBaoH-Ma/reftag=0201380214/media=hls4/ssd6/21/1/132727041.mp4/index.m3u8"

def download_file(url, filename):
    """Download file with progress tracking"""
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 1000000))  # Fallback size
            downloaded = 0
            
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive chunks
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                        print(f"Downloaded {downloaded} bytes ({progress:.1f}%)", end='\r')
        print("\nDownload complete")
        return True
    except Exception as e:
        print(f"\nDownload failed: {str(e)}")
        return False

def send_to_telegram(file_path):
    """Send file to Telegram"""
    try:
        with open(file_path, 'rb') as f:
            files = {'video': f}
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                data={"chat_id": CHAT_ID, "supports_streaming": False},
                files=files,
                timeout=60
            )
        return response.json()
    except Exception as e:
        print(f"Upload failed: {str(e)}")
        return None

def main():
    temp_file = "temp_video.mp4"
    
    # First try to send the URL directly
    print("Attempting to send URL directly...")
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": VIDEO_URL}
    )
    
    if response.status_code == 200:
        print("URL sent successfully!")
        return
    
    # If URL method fails, download and send the file
    print("Direct URL send failed, downloading video...")
    
    if download_file(VIDEO_URL, temp_file):
        print("Sending video to Telegram...")
        result = send_to_telegram(temp_file)
        
        if result and result.get('ok'):
            print("Successfully sent video to Telegram!")
            print(f"File ID: {result['result']['video']['file_id']}")
        else:
            print("Failed to send video:", result)
    
    # Clean up
    if os.path.exists(temp_file):
        os.remove(temp_file)

if __name__ == "__main__":
    main()
