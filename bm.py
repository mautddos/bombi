import time
import random
import logging
from fake_useragent import UserAgent
from selenium_stealth import stealth
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_viewer.log'),
        logging.StreamHandler()
    ]
)

class YouTubeViewer:
    def __init__(self):
        self.ua = UserAgent()
        self.proxies = []
        self.session_count = 0
        self.failed_count = 0

    def get_random_user_agent(self):
        """Generate a random user agent"""
        return self.ua.random

    def load_proxies(self, file_path):
        """Load proxies from a file"""
        try:
            with open(file_path, 'r') as file:
                self.proxies = [line.strip() for line in file if line.strip()]
            if not self.proxies:
                logging.warning("No proxies found in the file.")
            else:
                logging.info(f"Loaded {len(self.proxies)} proxies.")
        except FileNotFoundError:
            logging.error(f"Proxy file not found: {file_path}")

    def create_driver(self, proxy=None):
        """Create and configure a Chrome WebDriver"""
        options = Options()
        
        # Common options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--user-agent={self.get_random_user_agent()}")
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Proxy configuration
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
        
        # Additional stealth options
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            driver = webdriver.Chrome(options=options)
            
            # Apply stealth settings
            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True)
            
            return driver
        except Exception as e:
            logging.error(f"Failed to create WebDriver: {e}")
            return None

    def simulate_human_interaction(self, driver):
        """Simulate human-like interactions"""
        try:
            # Random mouse movements
            action = ActionChains(driver)
            for _ in range(random.randint(2, 5)):
                x_offset = random.randint(-100, 100)
                y_offset = random.randint(-100, 100)
                action.move_by_offset(x_offset, y_offset).perform()
                time.sleep(random.uniform(0.5, 1.5))
            
            # Random scrolls
            scroll_amount = random.randint(500, 1500)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(random.uniform(1, 3))
            
            # Sometimes click on the page
            if random.random() > 0.7:
                action.click().perform()
            
            # Random video watch time (30-80% of video length)
            watch_time = random.uniform(30, 180)
            logging.info(f"Watching video for {watch_time:.1f} seconds")
            time.sleep(watch_time)
            
        except Exception as e:
            logging.warning(f"Interaction simulation failed: {e}")

    def load_session(self, url, proxy=None):
        """Load a YouTube session with the given URL"""
        driver = None
        try:
            driver = self.create_driver(proxy)
            if not driver:
                self.failed_count += 1
                return
            
            logging.info(f"Session {self.session_count + 1}: Opening YouTube URL with proxy: {proxy if proxy else 'No proxy'}")
            driver.get(url)
            
            # Wait for page to load
            time.sleep(random.uniform(3, 8))
            
            # Check if YouTube is blocking us
            if "sorry" in driver.title.lower():
                logging.warning("YouTube has detected unusual traffic")
                self.failed_count += 1
                return
            
            # Simulate human behavior
            self.simulate_human_interaction(driver)
            
            self.session_count += 1
            logging.info(f"Session completed successfully. Total: {self.session_count}")
            
        except WebDriverException as e:
            self.failed_count += 1
            logging.error(f"WebDriver error occurred: {e}")
        except Exception as e:
            self.failed_count += 1
            logging.error(f"Unexpected error occurred: {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def run(self, url, view_count, refresh_rate, proxy_file=None):
        """Run the viewer with the given parameters"""
        if proxy_file:
            self.load_proxies(proxy_file)
        
        logging.info("Starting YouTube view automation...")
        start_time = time.time()
        
        while self.session_count < view_count:
            proxy = random.choice(self.proxies) if self.proxies else None
            self.load_session(url, proxy)
            
            # Random delay between sessions
            delay = refresh_rate + random.uniform(-5, 5)
            if delay < 5:  # Minimum delay
                delay = 5
                
            if self.session_count < view_count:
                logging.info(f"Waiting {delay:.1f} seconds before next session...")
                time.sleep(delay)
        
        total_time = time.time() - start_time
        logging.info(f"Completed {self.session_count} views in {total_time/60:.1f} minutes.")
        logging.info(f"Success rate: {(self.session_count/(self.session_count + self.failed_count))*100:.1f}%")

if __name__ == "__main__":
    viewer = YouTubeViewer()
    
    # Get user input
    youtube_url = input("Enter YouTube URL: ").strip()
    refresh_rate = float(input("Enter refresh rate (seconds): ").strip())
    view_count = int(input("Enter number of views: ").strip())
    use_proxies = input("Use proxies? (y/n): ").strip().lower() == 'y'
    
    proxy_file = './proxies.txt' if use_proxies else None
    
    # Run the viewer
    viewer.run(youtube_url, view_count, refresh_rate, proxy_file)
