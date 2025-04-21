import time
import random
import threading
import requests
import os
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

# Configuration
MAX_THREADS = 5  # Reduced for stability with free proxies
VIEWS_PER_THREAD = 1
PROXY_TIMEOUT = 30
CHROME_VERSION = 114  # Specific Chrome version to use

# Free proxy sources
def get_free_proxies():
    try:
        urls = [
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
        ]
        proxies = []
        for url in urls:
            try:
                response = requests.get(url, timeout=10)
                proxies.extend([p.strip() for p in response.text.splitlines() if p.strip()])
            except:
                continue
        return list(set(proxies))[:100]  # Return unique proxies, max 100
    except:
        return [
            "103.155.217.1:41367",  # Fallback proxies
            "45.43.31.145:3128",
            "47.88.29.108:8080"
        ]

PROXY_LIST = get_free_proxies()
print(f"🛜 Loaded {len(PROXY_LIST)} proxies")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

class ViewCounter:
    def __init__(self):
        self.count = 0
        self.success = 0
        self.failed = 0
        self.lock = threading.Lock()
    
    def increment(self, success=True):
        with self.lock:
            self.count += 1
            if success:
                self.success += 1
            else:
                self.failed += 1
    
    def get_stats(self):
        with self.lock:
            return f"Total: {self.count} | ✅ Success: {self.success} | ❌ Failed: {self.failed}"

view_counter = ViewCounter()

def setup_driver():
    options = uc.ChromeOptions()
    
    # Clear ChromeDriver cache to prevent "Text file busy" errors
    cache_dir = os.path.expanduser('~/.local/share/undetected_chromedriver')
    if os.path.exists(cache_dir):
        for f in os.listdir(cache_dir):
            try:
                os.remove(os.path.join(cache_dir, f))
            except:
                pass
    
    if PROXY_LIST:
        proxy = random.choice(PROXY_LIST)
        options.add_argument(f'--proxy-server=http://{proxy}')
    
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f'user-agent={user_agent}')
    
    try:
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            version_main=CHROME_VERSION,
            driver_executable_path='/usr/local/bin/chromedriver'  # Explicit path
        )
        return driver
    except Exception as e:
        print(f"🚨 Driver Error: {str(e)[:100]}")
        return None

def human_like_actions(driver):
    try:
        # Random scrolling
        for _ in range(random.randint(3, 7)):
            scroll_px = random.randint(300, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_px})")
            time.sleep(random.uniform(0.3, 1.5))
        
        # Random clicks
        buttons = driver.find_elements(By.TAG_NAME, "button")
        if buttons:
            random.choice(buttons).click()
            time.sleep(random.uniform(0.5, 2))
        
        # Keyboard actions
        actions = ActionChains(driver)
        actions.send_keys(Keys.SPACE).pause(1).send_keys(Keys.ARROW_DOWN).perform()
    except:
        pass

def send_view(link, thread_num):
    driver = setup_driver()
    if not driver:
        view_counter.increment(success=False)
        return False

    try:
        driver.set_page_load_timeout(PROXY_TIMEOUT)
        driver.get(link)
        time.sleep(random.randint(8, 15))
        
        human_like_actions(driver)
        
        # Try to play video
        try:
            driver.execute_script("document.querySelector('video').play()")
            play_time = random.randint(15, 30)
            time.sleep(play_time)
        except:
            try:
                play_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Play']")
                play_button.click()
                time.sleep(random.randint(15, 30))
            except:
                pass
        
        view_counter.increment(success=True)
        print(f"✅ [Thread-{thread_num}] View sent! | {view_counter.get_stats()}")
        return True
    except Exception as e:
        view_counter.increment(success=False)
        print(f"❌ [Thread-{thread_num}] Error: {str(e)[:100]}... | {view_counter.get_stats()}")
        return False
    finally:
        try:
            driver.quit()
        except:
            pass

def main():
    print("""
    TERABOX VIEW BOT (Fixed Version)
    ==============================
    Features:
    - Fixed ChromeDriver errors
    - Better proxy handling
    - Stable threading
    - Detailed view counter
    """)
    
    link = input("Terabox Video Link: ").strip()
    total_views = int(input("Total views to send: "))
    threads = min(int(input(f"Threads to use (1-{MAX_THREADS}): ")), MAX_THREADS)
    
    views_per_thread = max(1, total_views // threads)
    print(f"\n🔥 Starting {threads} threads ({views_per_thread} views each)...\n")
    print(f"🔄 Using {len(PROXY_LIST)} proxies\n")
    
    def worker(thread_num):
        for _ in range(views_per_thread):
            send_view(link, thread_num)
            time.sleep(random.randint(10, 30))
    
    thread_list = []
    for i in range(threads):
        t = threading.Thread(target=worker, args=(i+1,))
        t.start()
        thread_list.append(t)
        time.sleep(1)  # Increased delay between thread starts
    
    for t in thread_list:
        t.join()
    
    print(f"\n🎉 Campaign Complete! Final Stats: {view_counter.get_stats()}")

if __name__ == "__main__":
    # Install required ChromeDriver first
    os.system('wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip')
    os.system('unzip chromedriver_linux64.zip')
    os.system('chmod +x chromedriver')
    os.system('sudo mv chromedriver /usr/local/bin/')
    
    main()
