import time
import random
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType

# प्रॉक्सी लिस्ट (अपनी प्रॉक्सी डालें)
PROXY_LIST = [
    "123.45.67.89:8080",
    "98.76.54.32:3128",
    # और जोड़ें...
]

# यूजर-एजेंट लिस्ट (अलग-अलग ब्राउज़र वर्जन)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15...",
    # और जोड़ें...
]

def simulate_view(video_url):
    try:
        # 1. ब्राउज़र सेटअप (प्रॉक्सी + हेडलेस मोड)
        proxy = Proxy({
            'proxyType': ProxyType.MANUAL,
            'httpProxy': random.choice(PROXY_LIST),
            'sslProxy': random.choice(PROXY_LIST)
        })
        
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # बिना GUI के चलेगा
        options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
        options.proxy = proxy
        
        driver = webdriver.Chrome(options=options)
        
        # 2. वीडियो ओपन करें
        driver.get(video_url)
        print("वीडियो ओपन किया गया:", video_url)
        
        # 3. रैंडम माउस मूवमेंट (जैसे असली यूजर)
        actions = ActionChains(driver)
        actions.move_by_offset(random.randint(10, 100), random.randint(10, 100)).perform()
        
        # 4. वीडियो को 30-120 सेकंड तक चलने दें
        watch_time = random.randint(30, 120)
        print(f"वीडियो देखा जा रहा है... ({watch_time} सेकंड)")
        time.sleep(watch_time)
        
        # 5. ब्राउज़र बंद करें
        driver.quit()
        return True
    
    except Exception as e:
        print("ERROR:", e)
        return False

if __name__ == "__main__":
    VIDEO_URL = "https://www.terabox.com/your-video-link"  # अपना वीडियो URL डालें
    
    for i in range(10):  # 10 व्यूज भेजने के लिए
        print(f"\nव्यू {i+1} सिमुलेट किया जा रहा है...")
        success = simulate_view(VIDEO_URL)
        if success:
            print("सफलतापूर्वक व्यू भेजा गया!")
        else:
            print("व्यू भेजने में असफल!")
        
        # अगले व्यू से पहले डिले (5-30 सेकंड)
        delay = random.randint(5, 30)
        print(f"अगले व्यू से पहले {delay} सेकंड का इंतजार...")
        time.sleep(delay)
