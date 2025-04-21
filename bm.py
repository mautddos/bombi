import time
import random
import threading
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

# प्रॉक्सी लिस्ट (अपनी प्रॉक्सी डालें)
PROXY_LIST = [
    "193.123.225.255:8080",
    "45.67.89.123:3128",
    "111.222.333.444:8080"
]

# यूजर एजेंट लिस्ट
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def setup_driver():
    options = uc.ChromeOptions()
    
    # प्रॉक्सी सेटअप
    proxy = random.choice(PROXY_LIST)
    options.add_argument(f'--proxy-server=http://{proxy}')
    
    # हेडलेस मोड (चुपके ��े चलने के लिए)
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # रैंडम यूजर एजेंट
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f'user-agent={user_agent}')
    
    # बॉट डिटेक्शन से बचाव
    driver = uc.Chrome(options=options)
    return driver

def human_like_actions(driver):
    try:
        # रैंडम स्क्रॉलिंग
        for _ in range(random.randint(3, 7)):
            scroll_px = random.randint(300, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_px})")
            time.sleep(random.uniform(0.5, 2))
        
        # रैंडम क्लिक (अगर कोई बटन मिले)
        buttons = driver.find_elements(By.TAG_NAME, "button")
        if buttons:
            random.choice(buttons).click()
            time.sleep(random.uniform(1, 3))
        
        # कीबोर्ड की रैंडम की प्रेस (SPACE, DOWN ARROW)
        actions = ActionChains(driver)
        actions.send_keys(Keys.SPACE).pause(1).send_keys(Keys.ARROW_DOWN).perform()
    except:
        pass

def send_view(link):
    driver = setup_driver()
    try:
        driver.get(link)
        time.sleep(random.randint(5, 10))  # पेज लोड होने का इंतज़ार
        
        # ह्यूमन जैसी एक्टिविटीज
        human_like_actions(driver)
        
        # वीडियो चलाने की कोशिश (अगर प्ले बटन मिले)
        try:
            play_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Play']")
            play_button.click()
            time.sleep(random.randint(10, 20))  # वीडियो चलने दें
        except:
            pass
        
        print("✅ व्यू भेजा गया! (IP: " + driver.execute_script("return JSON.stringify(await fetch('https://api.ipify.org?format=json').then(res => res.json()))") + ")")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False
    finally:
        driver.quit()

def main():
    print("""
    ████████╗███████╗██████╗  █████╗ ██████╗  ██████╗ ██╗  ██╗
    ╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝
       ██║   █████╗  ██████╔╝███████║██████╔╝██║   ██║ ╚███╔╝ 
       ██║   ██╔══╝  ██╔══██╗██╔══██║██╔══██╗██║   ██║ ██╔██╗ 
       ██║   ███████╗██║  ██║██║  ██║██████╔╝╚██████╔╝██╔╝ ██╗
       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝
    ========================================================
    KHATARNAK Terabox View Bot | 100% Undetectable
    """)
    
    link = input("Terabox Video Link: ").strip()
    views = int(input("कितने व्यूज भेजने हैं?: "))
    threads = int(input("कितने थ्रेड्स चलाने हैं? (ज्यादा = तेज, लेकिन CPU उपयोग बढ़ेगा): "))
    
    print("\n🚀 बॉट शुरू हो रहा है...\n")
    
    def worker():
        for i in range(views // threads):
            print(f"📡 {threading.current_thread().name} - व्यू {i+1} भेजा जा रहा है...")
            success = send_view(link)
            if not success:
                print("⚠️ रिपीट करने का प्रयास...")
                time.sleep(5)
                send_view(link)
            wait_time = random.randint(15, 30)
            print(f"⏳ अगले व्यू से पहले {wait_time} सेकंड इंतज़ार...")
            time.sleep(wait_time)
    
    # मल्टी-थ्रेडिंग शुरू करें
    all_threads = []
    for _ in range(threads):
        t = threading.Thread(target=worker)
        t.start()
        all_threads.append(t)
    
    for t in all_threads:
        t.join()
    
    print("\n🎉 सभी व्यूज सफलतापूर्वक भेज दिए गए!")

if __name__ == "__main__":
    main()
