import time
import random
import threading
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc

# Configuration
MAX_THREADS = 100  # Maximum concurrent threads
VIEWS_PER_THREAD = 1  # Views per thread
PROXY_TIMEOUT = 30  # Proxy timeout in seconds

# Premium Proxy List (Replace with your proxies)
PROXY_LIST = [
    "user:pass@ip:port",  # Premium proxy format 1
    "ip:port",            # Premium proxy format 2
    # Add more proxies here (minimum 100 recommended for 100 threads)
]

USER_AGENTS = [
    # Updated user agents list
]

class ViewCounter:
    def __init__(self):
        self.count = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.count += 1
    
    def get_count(self):
        with self.lock:
            return self.count

view_counter = ViewCounter()

def setup_driver():
    options = uc.ChromeOptions()
    
    # Proxy setup with authentication support
    if PROXY_LIST:
        proxy = random.choice(PROXY_LIST)
        if "@" in proxy:  # Proxy with authentication
            username, rest = proxy.split("@")[0], proxy.split("@")1]
            password, proxy_ip = rest.split(":") if ":" in rest else ("", rest)
            options.add_argument(f'--proxy-server=http://{proxy_ip}')
            options.add_argument(f'--proxy-auth={username}:{password}')
        else:
            options.add_argument(f'--proxy-server=http://{proxy}')
    
    # Enhanced stealth options
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--remote-debugging-port=9222')
    
    # Random user agent
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f'user-agent={user_agent}')
    
    try:
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            version_main=114  # Specify Chrome version
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
        
        # Mouse movements
        actions.move_by_offset(random.randint(5, 50), random.randint(5, 50)).perform()
    except:
        pass

def send_view(link, thread_num):
    global view_counter
    driver = setup_driver()
    if not driver:
        return False

    try:
        # Set timeout
        driver.set_page_load_timeout(PROXY_TIMEOUT)
        
        # Open URL
        driver.get(link)
        time.sleep(random.randint(8, 15))
        
        # Human-like behavior
        human_like_actions(driver)
        
        # Play video (multiple methods)
        try:
            driver.execute_script("document.querySelector('video').play()")
            time.sleep(random.randint(15, 30))
        except:
            try:
                play_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Play']")
                play_button.click()
                time.sleep(random.randint(15, 30))
            except:
                pass
        
        view_counter.increment()
        print(f"✅ [Thread-{thread_num}] View sent! (Total: {view_counter.get_count()})")
        return True
    except Exception as e:
        print(f"❌ [Thread-{thread_num}] Error: {str(e)[:100]}...")
        return False
    finally:
        try:
            driver.quit()
        except:
            pass

def main():
    print("""
    TERABOX MASS VIEW BOT
    ====================
    Features:
    - Mass proxy support
    - View counter
    - Human-like behavior
    - Multi-threading
    """)
    
    link = input("Terabox Video Link: ").strip()
    total_views = int(input("Total views to send: "))
    threads = min(int(input("Threads to use (1-100): ")), MAX_THREADS)
    
    views_per_thread = max(1, total_views // threads)
    print(f"\n🔥 Starting {threads} threads ({views_per_thread} views each)...\n")
    
    def worker(thread_num):
        for _ in range(views_per_thread):
            send_view(link, thread_num)
            time.sleep(random.randint(10, 30))
    
    # Start threads
    thread_list = []
    for i in range(threads):
        t = threading.Thread(target=worker, args=(i+1,))
        t.start()
        thread_list.append(t)
        time.sleep(0.5)  # Stagger thread starts
    
    # Wait for completion
    for t in thread_list:
        t.join()
    
    print(f"\n🎉 Campaign Complete! Total views sent: {view_counter.get_count()}")

if __name__ == "__main__":
    main()
