import requests
import os
from urllib.parse import urlparse

# Configuration
BOT_TOKEN = "7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI"
CHAT_ID = "8167507955"
VIDEO_URL = "https://ip296321550.ahcdn.com/key=ZVah3Txj1tCBKt+HLrXfrQ,s=,end=1743840000/data=18.180.253.18-dvp/state=Z-CxJAFJAHQjlBaoH-Ma/reftag=0201380214/media=hls4/ssd6/21/1/132727041.mp4/index.m3u8"

def download_file(url, filename):
    """Download file with progress tracking"""
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                print(f"Downloaded {downloaded}/{total_size} bytes ({downloaded/total_size*100:.2f}%)", end='\r')
    print("\nDownload complete")

def send_to_telegram(file_path, caption=""):
    """Send file to Telegram with proper file type detection"""
    file_ext = os.path.splitext(file_path)[1].lower()
    file_type = 'video' if file_ext in ['.mp4','.mov','.avi'] else 'document'
    
    with open(file_path, 'rb') as f:
        files = {file_type: f}
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/send{file_type.capitalize()}",
            data={"chat_id": CHAT_ID, "caption": caption},
            files=files
        )
    return response.json()

def process_hls_to_mp4(m3u8_url, output_file):
    """Convert HLS to MP4 using ffmpeg"""
    try:
        import ffmpeg
        (
            ffmpeg
            .input(m3u8_url)
            .output(output_file, c='copy', f='mp4')
            .run(quiet=True, overwrite_output=True)
        )
        return True
    except Exception as e:
        print(f"FFmpeg error: {e}")
        return False

def main():
    try:
        # Step 1: Determine if URL is HLS
        parsed = urlparse(VIDEO_URL)
        is_hls = parsed.path.endswith('.m3u8')
        
        temp_file = "temp_video.mp4"
        
        # Step 2: Process HLS or direct download
        if is_hls:
            print("Processing HLS stream...")
            if not process_hls_to_mp4(VIDEO_URL, temp_file):
                print("FFmpeg not available, trying direct download")
                download_file(VIDEO_URL, temp_file)
        else:
            download_file(VIDEO_URL, temp_file)
        
        # Step 3: Send to Telegram
        print("Sending to Telegram...")
        result = send_to_telegram(temp_file, "Video sent from VPS")
        
        if result.get('ok'):
            print("Successfully sent video!")
            print(f"File ID: {result['result']['video']['file_id']}")
        else:
            print("Failed to send:", result)
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    main()
