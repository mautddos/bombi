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
MAX_THREADS = 5
MAX_RETRIES = 3
PROXY_TIMEOUT = 20
VIEW_DELAY = (15, 30)

# Declare as global first
global PROXY_LIST
PROXY_LIST = []

# Premium proxy sources
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
]

def refresh_proxies():
    global PROXY_LIST  # Now properly declared
    proxies = []
    for url in PROXY_SOURCES:
        try:
            response = requests.get(url, timeout=10)
            proxies.extend([p.strip() for p in response.text.splitlines() if p.strip()])
        except:
            continue
    PROXY_LIST = list(set(proxies))[:200]
    print(f"🌀 Loaded {len(PROXY_LIST)} proxies")

refresh_proxies()  # Initial load

# Rest of your code remains the same...
# User agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

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
                global PROXY_LIST
                PROXY_LIST = refresh_proxies()
                print(f"♻️ Refreshed proxy list ({len(PROXY_LIST)} available)")
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
    options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    
    try:
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            version_main=114,
            driver_executable_path='/usr/local/bin/chromedriver'
        )
        return driver
    except Exception as e:
        print(f"⚠️ Proxy {proxy} failed: {str(e)[:80]}")
        return None

def human_interaction(driver):
    try:
        # Scroll randomly
        for _ in range(random.randint(2, 5)):
            driver.execute_script(f"window.scrollBy(0, {random.randint(200, 800)})")
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
    except:
        pass

def send_view(link, attempt=1):
    driver = setup_driver()
    if not driver:
        if attempt < MAX_RETRIES:
            time.sleep(2)
            return send_view(link, attempt + 1)
        view_manager.record_result(False)
        return False

    try:
        driver.set_page_load_timeout(PROXY_TIMEOUT)
        driver.get(link)
        time.sleep(random.randint(5, 10))
        
        # Human-like behavior
        human_interaction(driver)
        
        # Try to play video
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

def worker(link, views_needed):
    views_sent = 0
    while views_sent < views_needed:
        if send_view(link):
            views_sent += 1
        time.sleep(random.randint(*VIEW_DELAY))

def main():
    print("""
    ████████╗███████╗██████╗  █████╗ ██████╗  ██████╗ ██╗  ██╗
    ╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝
       ██║   █████╗  ██████╔╝███████║██████╔╝██║   ██║ ╚███╔╝ 
       ██║   ██╔══╝  ██╔══██╗██╔══██║██╔══██╗██║   ██║ ██╔██╗ 
       ██║   ███████╗██║  ██║██║  ██║██████╔╝╚██████╔╝██╔╝ ██╗
       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝
    ========================================================
    TeraBox View Bot with Auto-Retry System
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

if __name__ == "__main__":
    # Ensure ChromeDriver is installed
    if not os.path.exists("/usr/local/bin/chromedriver"):
        os.system('wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip')
        os.system('unzip chromedriver_linux64.zip')
        os.system('chmod +x chromedriver')
        os.system('sudo mv chromedriver /usr/local/bin/')
    
    main()
