import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 1. Enter your credentials manually
TERABOX_EMAIL = "combill925@gmail.com"
TERABOX_PASSWORD = "www.chut.com"

# 2. Setup Chrome Options
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Disabled for debugging
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")  # Set window size
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

# 3. Install and use proper chromedriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 20)

try:
    # 4. Go to Terabox website
    print("🌐 Accessing Terabox website...")
    driver.get("https://www.terabox.com")
    
    # Wait for page to load completely
    time.sleep(5)
    
    # Check if we're redirected to a different login URL
    if "login" in driver.current_url.lower():
        print("ℹ️ Redirected to login page directly")
    
    # 5. Try multiple ways to find login elements
    print("🔍 Looking for login form...")
    try:
        # Try finding email input with different selectors
        email_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[name='username'], input[type='email'], #username, .username")
        ))
        password_input = driver.find_element(By.CSS_SELECTOR, "input[name='password'], input[type='password'], #password, .password")
        
        email_input.send_keys(TERABOX_EMAIL)
        password_input.send_keys(TERABOX_PASSWORD)
        print("🔑 Entered credentials")
        
        # Try finding login button with different selectors
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .login-btn, #login-button")
        login_button.click()
        print("🖱️ Clicked login button")
        time.sleep(5)
        
    except Exception as e:
        print(f"⚠️ Couldn't find elements with standard selectors: {e}")
        # Take screenshot for debugging
        driver.save_screenshot("terabox_login_error.png")
        print("📸 Saved screenshot as 'terabox_login_error.png'")

    # 6. Confirm login
    try:
        profile_element = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".user-profile, .avatar, .user-icon")
        ))
        print("✅ Login successful!")
    except NoSuchElementException:
        print("❌ Login failed. Check credentials or site structure.")
        # Take screenshot for debugging
        driver.save_screenshot("terabox_login_failed.png")
        print("📸 Saved screenshot as 'terabox_login_failed.png'")

    # 7. Print session cookies
    cookies = driver.get_cookies()
    print("\n🔒 Session Cookies:")
    for cookie in cookies:
        print(f"{cookie['name']}: {cookie['value']}")

except Exception as e:
    print(f"❌ Error: {e}")
    # Take screenshot for debugging
    driver.save_screenshot("terabox_error.png")
    print("📸 Saved screenshot as 'terabox_error.png'")

finally:
    driver.quit()
    print("🚪 Browser closed")
