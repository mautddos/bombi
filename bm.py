import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

# प्रॉक्सी लिस्ट (चाहो तो खाली छोड़ो अगर private proxies हो)
PROXY_LIST = [
    "123.45.67.89:8080",
    "98.76.54.32:3128",
    # और प्रॉक्सी डालो यहाँ
]

# यूजर एजेंट्स लिस्ट (अधिक realistic)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

def get_video_link():
    return input("TeraBox वीडियो लिंक डालें: ").strip()

def setup_driver(proxy=None):
    options = webdriver.ChromeOptions()
    
    # Headless + Anti-detection settings
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    
    # Proxy settings
    if proxy:
        options.add_argument(f'--proxy-server=http://{proxy}')

    try:
        # Auto-download ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except WebDriverException as e:
        print(f"ChromeDriver Error: {e}")
        return None

def simulate_view(video_url, proxy=None):
    driver = setup_driver(proxy)
    if not driver:
        return False

    try:
        # Open video with randomized delay
        time.sleep(random.uniform(1, 3))
        driver.get(video_url)
        print(f"वीडियो ओपन किया गया: {video_url}")

        # Simulate human-like interactions
        actions = ActionChains(driver)
        
        # Random mouse movements
        for _ in range(random.randint(3, 7)):
            x_offset = random.randint(10, 200)
            y_offset = random.randint(10, 200)
            actions.move_by_offset(x_offset, y_offset).perform()
            time.sleep(random.uniform(0.5, 1.5))

        # Random scroll
        driver.execute_script(f"window.scrollBy(0, {random.randint(100, 500)})")
        time.sleep(random.uniform(1, 3))

        # Watch time (randomized)
        watch_time = random.randint(45, 180)  # 45-180 seconds
        print(f"वीडियो देखा जा रहा है... {watch_time} सेकंड")
        
        # Simulate activity during watch time
        for _ in range(random.randint(2, 5)):
            time.sleep(watch_time // random.randint(3, 6))
            driver.execute_script("window.scrollBy(0, 100)")
            actions.move_by_offset(random.randint(-50, 50), random.randint(-50, 50)).perform()

        driver.quit()
        return True

    except Exception as e:
        print("ERROR:", e)
        if driver:
            driver.quit()
        return False

if __name__ == "__main__":
    video_url = get_video_link()
    view_count = int(input("कितने व्यूज भेजने हैं?: "))

    successful_views = 0
    for i in range(view_count):
        print(f"\nव्यू {i+1} सिमुलेट किया जा रहा है...")

        proxy = random.choice(PROXY_LIST) if PROXY_LIST else None
        success = simulate_view(video_url, proxy)

        if success:
            successful_views += 1
            print("✅ सफलतापूर्वक व्यू भेजा गया!")
        else:
            print("❌ व्यू भेजने में असफल!")

        # Randomized delay between views (longer to avoid detection)
        delay = random.randint(15, 60)  # 15-60 seconds
        print(f"⏳ अगले व्यू से पहले {delay} सेकंड का इंतजार...")
        time.sleep(delay)

    print(f"\nकुल {successful_views}/{view_count} व्यू सफलतापूर्वक भेजे गए!")
