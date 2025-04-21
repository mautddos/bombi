import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# प्रॉक्सी लिस्ट (चाहो तो खाली छोड़ो अगर private proxies हो)
PROXY_LIST = [
    "123.45.67.89:8080",
    "98.76.54.32:3128",
    # और प्रॉक्सी डालो यहाँ
]

# यूजर एजेंट्स लिस्ट
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15...",
    # और भी डाल सकते हो
]

def get_video_link():
    return input("TeraBox वीडियो लिंक डालें: ").strip()

def setup_driver(proxy=None):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')

    if proxy:
        options.add_argument(f'--proxy-server=http://{proxy}')

    driver = webdriver.Chrome(options=options)
    return driver

def simulate_view(video_url, proxy=None):
    try:
        driver = setup_driver(proxy)
        driver.get(video_url)
        print(f"वीडियो ओपन किया गया: {video_url}")

        # Random mouse movement
        actions = ActionChains(driver)
        actions.move_by_offset(random.randint(10, 100), random.randint(10, 100)).perform()

        # Watch for random seconds
        watch_time = random.randint(30, 120)
        print(f"वीडियो देखा जा रहा है... {watch_time} सेकंड")
        time.sleep(watch_time)

        driver.quit()
        return True

    except Exception as e:
        print("ERROR:", e)
        return False

if __name__ == "__main__":
    video_url = get_video_link()
    view_count = int(input("कितने व्यूज भेजने हैं?: "))

    for i in range(view_count):
        print(f"\nव्यू {i+1} सिमुलेट किया जा रहा है...")

        proxy = random.choice(PROXY_LIST) if PROXY_LIST else None
        success = simulate_view(video_url, proxy)

        if success:
            print("सफलतापूर्वक व्यू भेजा गया!")
        else:
            print("व्यू भेजने में असफल!")

        delay = random.randint(5, 30)
        print(f"अगले व्यू से पहले {delay} सेकंड का इंतजार...")
        time.sleep(delay)
