import time
import random
import threading
import requests
import os
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

# ========== GLOBAL CONFIGURATION ==========
MAX_THREADS = 5
MAX_RETRIES = 3
PROXY_TIMEOUT = 20
VIEW_DELAY = (15, 30)  # Min/Max delay between views (seconds)
CHROME_VERSION = 114

# ========== GLOBAL VARIABLES ==========
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Initialize global proxy list
PROXY_LIST = []

# ========== PROXY MANAGEMENT ==========
def refresh_proxies():
    global PROXY_LIST
    proxies = []
    for url in PROXY_SOURCES:
        try:
            response = requests.get(url, timeout=10)
            proxies.extend([p.strip() for p in response.text.splitlines() if p.strip()])
        except Exception as e:
            print(f"⚠️ Proxy source error: {str(e)[:80]}")
            continue
    
    PROXY_LIST = list(set(proxies))[:200]  # Remove duplicates and limit to 200
    print(f"🌀 Loaded {len(PROXY_LIST)} fresh proxies")
    return PROXY_LIST

# Initial proxy load
refresh_proxies()

# ========== VIEW MANAGEMENT ==========
class ViewManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.success = 0
        self.failed = 0
        self.proxy_index = 0
    
    def get_proxy(self):
        with self.lock:
            if self.proxy_index >= len(PROXY_LIST):
                self.proxy_index = 0
                refresh_proxies()
            proxy = PROXY_LIST[self.proxy_index]
            self.proxy_index += 1
            return proxy
    
    def record_result(self, success):
        with self.lock:
            if success:
                self.success += 1
            else:
                self.failed += 1
    
    def get_stats(self):
        with self.lock:
            return f"✅ Success: {self.success} | ❌ Failed: {self.failed}"

view_manager = ViewManager()

# ========== BROWSER FUNCTIONS ==========
def setup_driver():
    options = uc.ChromeOptions()
    
    # Proxy setup
    proxy = view_manager.get_proxy()
    options.add_argument(f'--proxy-server=http://{proxy}')
    
    # Stealth settings
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    
    try:
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            version_main=CHROME_VERSION,
            driver_executable_path='/usr/local/bin/chromedriver'
        )
        return driver
    except Exception as e:
        print(f"⚠️ Proxy {proxy} failed: {str(e)[:80]}")
        return None

def human_interaction(driver):
    try:
        # Random scrolling
        for _ in range(random.randint(2, 5)):
            scroll_amount = random.randint(200, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(random.uniform(0.5, 1.5))
        
        # Random clicks
        buttons = driver.find_elements(By.TAG_NAME, "button")[:3]
        for btn in buttons:
            try:
                btn.click()
                time.sleep(random.uniform(0.3, 1.2))
            except:
                pass
        
        # Keyboard actions
        ActionChains(driver).send_keys(Keys.SPACE).pause(1).perform()
    except Exception as e:
        print(f"⚠️ Interaction error: {str(e)[:80]}")

# ========== CORE VIEW FUNCTION ==========
def send_view(link, attempt=1):
    driver = setup_driver()
    if not driver:
        if attempt < MAX_RETRIES:
            time.sleep(2)
            return send_view(link, attempt + 1)
        view_manager.record_result(False)
        return False

    try:
        # Set timeout and load page
        driver.set_page_load_timeout(PROXY_TIMEOUT)
        driver.get(link)
        time.sleep(random.randint(5, 10))
        
        # Human-like behavior
        human_interaction(driver)
        
        # Try to play video (multiple methods)
        try:
            driver.execute_script("document.querySelector('video').play()")
            time.sleep(random.randint(10, 20))
        except:
            try:
                driver.find_element(By.CSS_SELECTOR, "[aria-label='Play']").click()
                time.sleep(random.randint(10, 20))
            except:
                pass
        
        view_manager.record_result(True)
        print(f"🎯 View sent! ({view_manager.get_stats()})")
        return True
    except Exception as e:
        print(f"⚠️ Attempt {attempt} failed: {str(e)[:80]}")
        if attempt < MAX_RETRIES:
            time.sleep(2)
            return send_view(link, attempt + 1)
        view_manager.record_result(False)
        return False
    finally:
        try:
            driver.quit()
        except:
            pass

# ========== THREAD WORKER ==========
def worker(link, views_needed):
    views_sent = 0
    while views_sent < views_needed:
        if send_view(link):
            views_sent += 1
        time.sleep(random.randint(*VIEW_DELAY))

# ========== MAIN FUNCTION ==========
def main():
    print("""
    ████████╗███████╗██████╗  █████╗ ██████╗  ██████╗ ██╗  ██╗
    ╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝
       ██║   █████╗  ██████╔╝███████║██████╔╝██║   ██║ ╚███╔╝ 
       ██║   ██╔══╝  ██╔══██╗██╔══██║██╔══██╗██║   ██║ ██╔██╗ 
       ██║   ███████╗██║  ██║██║  ██║██████╔╝╚██████╔╝██╔╝ ██╗
       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝
    ========================================================
    TeraBox Ultimate View Bot v2.0
    """)
    
    link = input("Enter TeraBox video URL: ").strip()
    total_views = int(input("Total views needed: "))
    threads = min(int(input(f"Threads (1-{MAX_THREADS}): ")), MAX_THREADS)
    
    views_per_thread = max(1, total_views // threads)
    print(f"\n🚀 Starting {threads} threads (each sending ~{views_per_thread} views)")
    print(f"🔁 Auto-retry up to {MAX_RETRIES} times per view\n")
    
    workers = []
    for i in range(threads):
        t = threading.Thread(
            target=worker,
            args=(link, views_per_thread),
            name=f"Worker-{i+1}"
        )
        t.start()
        workers.append(t)
        time.sleep(0.5)  # Stagger thread starts
    
    for t in workers:
        t.join()
    
    print(f"\n🎉 Campaign complete! Final results: {view_manager.get_stats()}")

# ========== INITIALIZATION ==========
if __name__ == "__main__":
    # Ensure ChromeDriver is installed
    if not os.path.exists("/usr/local/bin/chromedriver"):
        print("⚙️ Installing ChromeDriver...")
        os.system('wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip')
        os.system('unzip chromedriver_linux64.zip')
        os.system('chmod +x chromedriver')
        os.system('sudo mv chromedriver /usr/local/bin/')
        os.system('rm chromedriver_linux64.zip')
    
    main()
