import time
import random
import threading
import requests
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
import os

# Configuration
MAX_THREADS = 5  # Reduced further for stability
VIEWS_PER_THREAD = 1
PROXY_TIMEOUT = 30
RETRY_DELAY = 10  # Seconds between retries

# Create directory for chromedriver if it doesn't exist
os.makedirs('/tmp/chromedriver', exist_ok=True)

def get_free_proxies():
    try:
        sources = [
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
        ]
        proxies = []
        for url in sources:
            try:
                response = requests.get(url, timeout=10)
                proxies.extend([p.strip() for p in response.text.splitlines() if p.strip()])
            except:
                continue
        return list(set(proxies))  # Remove duplicates
    except:
        return []

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

def setup_driver(thread_num):
    options = uc.ChromeOptions()
    
    # Set different user data dir for each thread
    options.add_argument(f'--user-data-dir=/tmp/chromedriver/thread_{thread_num}')
    
    # Random window size
    width = random.randint(1200, 1920)
    height = random.randint(800, 1080)
    options.add_argument(f'--window-size={width},{height}')
    
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
            version_main=114,
            driver_executable_path='/usr/bin/chromedriver'  # Explicit path
        )
        return driver
    except Exception as e:
        print(f"🚨 [Thread-{thread_num}] Driver Error: {str(e)[:100]}")
        return None

def human_like_actions(driver):
    try:
        # Random mouse movements
        actions = ActionChains(driver)
        for _ in range(random.randint(2, 5)):
            x_offset = random.randint(-100, 100)
            y_offset = random.randint(-100, 100)
            actions.move_by_offset(x_offset, y_offset).perform()
            time.sleep(random.uniform(0.2, 0.8))
        
        # Random scrolling
        scrolls = random.randint(3, 7)
        for i in range(scrolls):
            scroll_px = random.randint(300, 800) * (1 if i % 2 == 0 else -1)
            driver.execute_script(f"window.scrollBy(0, {scroll_px})")
            time.sleep(random.uniform(0.5, 1.5))
        
        # Random clicks
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            if buttons:
                btn = random.choice(buttons)
                actions.move_to_element(btn).pause(0.5).click().perform()
                time.sleep(random.uniform(1, 3))
        except:
            pass
    except Exception as e:
        pass

def send_view(link, thread_num, attempt=1):
    if attempt > 3:  # Max 3 attempts
        view_counter.increment(success=False)
        return False

    driver = setup_driver(thread_num)
    if not driver:
        time.sleep(RETRY_DELAY)
        return send_view(link, thread_num, attempt + 1)

    try:
        driver.set_page_load_timeout(PROXY_TIMEOUT)
        driver.get(link)
        time.sleep(random.randint(5, 10))
        
        human_like_actions(driver)
        
        # Try to play video
        try:
            driver.execute_script("""
                var v = document.querySelector('video');
                if (v) {
                    v.play();
                    v.currentTime = 10;  // Skip ahead
                    v.playbackRate = 1.2;  // Slightly faster
                }
            """)
            play_time = random.randint(15, 30)
            time.sleep(play_time)
        except:
            pass
        
        view_counter.increment(success=True)
        print(f"✅ [Thread-{thread_num}] View sent! | {view_counter.get_stats()}")
        return True
    except Exception as e:
        print(f"❌ [Thread-{thread_num}] Attempt {attempt} Error: {str(e)[:100]}...")
        time.sleep(RETRY_DELAY)
        return send_view(link, thread_num, attempt + 1)
    finally:
        try:
            driver.quit()
        except:
            pass

def main():
    print("""
    IMPROVED TERABOX VIEW BOT
    ========================
    Features:
    - Better proxy handling
    - Retry mechanism
    - Isolated browser profiles
    - More human-like behavior
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
            time.sleep(random.randint(15, 45))  # Longer delay between views
    
    thread_list = []
    for i in range(threads):
        t = threading.Thread(target=worker, args=(i+1,))
        t.start()
        thread_list.append(t)
        time.sleep(5)  # Stagger thread starts
    
    for t in thread_list:
        t.join()
    
    print(f"\n🎉 Campaign Complete! Final Stats: {view_counter.get_stats()}")

if __name__ == "__main__":
    # Install required ChromeDriver first
    try:
        uc.install()
    except Exception as e:
        print(f"Note: {str(e)}")
    
    main()
