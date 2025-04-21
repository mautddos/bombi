import time
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

USER_AGENTS = [
    # कुछ random user agents
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
]

def setup_driver(proxy=None):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--disable-gpu')
    options.add_argument("--remote-allow-origins=*")
    options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")

    if proxy:
        options.add_argument(f'--proxy-server=http://{proxy}')

    try:
        # Snap chromium के साथ manually path देना पड़ता है
        service = Service('/usr/lib/chromium-browser/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except WebDriverException as e:
        print(f"ChromeDriver Error: {e}")
        return None

def send_view(link):
    driver = setup_driver()
    if driver is None:
        return False

    try:
        driver.get(link)
        time.sleep(random.randint(5, 10))
        print("✅ View भेजा गया!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    os.system('clear')
    print("TeraBox वीडियो लिंक डालें: ", end="")
    link = input().strip()
    print("कितने व्यूज भेजने हैं?: ", end="")
    views = int(input().strip())

    for i in range(1, views + 1):
        print(f"व्यू {i} सिमुलेट किया जा रहा है...")
        success = send_view(link)
        if not success:
            print("❌  व्यू भेजने में असफल!")
        wait_time = random.randint(20, 40)
        print(f"⏳  अगले व्यू से पहले {wait_time} सेकंड का इंतजार...")
        time.sleep(wait_time)
