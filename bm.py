import requests
import os

# Your credentials
BOT_TOKEN = "7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI"
CHAT_ID = "8167507955"
VIDEO_URL = "https://ip296321550.ahcdn.com/key=ZVah3Txj1tCBKt+HLrXfrQ,s=,end=1743840000/data=18.180.253.18-dvp/state=Z-CxJAFJAHQjlBaoH-Ma/reftag=0201380214/media=hls4/ssd6/21/1/132727041.mp4/index.m3u8"

def send_video():
    try:
        # 1. First try sending just the URL
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": f"Video URL: {VIDEO_URL}"}
        )
        
        # 2. Download the video
        print("Downloading video...")
        response = requests.get(VIDEO_URL, stream=True)
        
        if response.status_code == 200:
            temp_file = "temp_video.mp4"
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            
            # 3. Send the video file
            print("Uploading to Telegram...")
            with open(temp_file, 'rb') as video_file:
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo",
                    data={"chat_id": CHAT_ID, "caption": "Sent from VPS"},
                    files={"video": video_file}
                )
            
            os.remove(temp_file)
            print("Video sent successfully!")
        else:
            print(f"Download failed. Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {str(e)}")

# Run the function
send_video()
