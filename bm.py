import requests
import os
import subprocess
import time

# Configuration
BOT_TOKEN = "7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI"
CHAT_ID = "8167507955"
HLS_URL = "https://ip296321550.ahcdn.com/key=ZVah3Txj1tCBKt+HLrXfrQ,s=,end=1743840000/data=18.180.253.18-dvp/state=Z-CxJAFJAHQjlBaoH-Ma/reftag=0201380214/media=hls4/ssd6/21/1/132727041.mp4/index.m3u8"
OUTPUT_FILE = "full_video.mp4"
TIMEOUT = 300  # 5 minutes timeout

def check_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except:
        return False

def convert_hls_to_mp4(hls_url, output_file):
    """Convert HLS stream to MP4 using ffmpeg"""
    try:
        command = [
            "ffmpeg",
            "-i", hls_url,
            "-c", "copy",
            "-f", "mp4",
            output_file,
            "-y"  # Overwrite output file if exists
        ]
        
        print("Starting HLS to MP4 conversion...")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Monitor progress
        while True:
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        if process.returncode != 0:
            raise Exception("FFmpeg conversion failed")
        
        print("Conversion completed successfully!")
        return True
        
    except Exception as e:
        print(f"Conversion error: {str(e)}")
        return False

def send_to_telegram(file_path):
    """Send file to Telegram with progress tracking"""
    try:
        file_size = os.path.getsize(file_path)
        print(f"Uploading {file_size/1024/1024:.1f}MB file...")
        
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                data={
                    'chat_id': CHAT_ID,
                    'supports_streaming': 'False'  # Force full download
                },
                files={'video': f},
                timeout=TIMEOUT
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
    # Step 1: Check requirements
    if not check_ffmpeg():
        print("Error: ffmpeg is required but not installed")
        print("Install it with: sudo apt-get install ffmpeg")
        return
    
    # Step 2: Convert HLS to MP4
    if not convert_hls_to_mp4(HLS_URL, OUTPUT_FILE):
        return
    
    # Step 3: Send to Telegram
    if not send_to_telegram(OUTPUT_FILE):
        return
    
    # Clean up
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        print("Temporary file removed")

if __name__ == "__main__":
    main()
