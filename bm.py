import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Load credentials from .env
load_dotenv()
TERABOX_EMAIL = os.getenv("TERABOX_EMAIL")
TERABOX_PASSWORD = os.getenv("TERABOX_PASSWORD")

if not TERABOX_EMAIL or not TERABOX_PASSWORD:
    raise ValueError("Email or password not found in .env file!")

# Configure Chrome WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in background (optional)
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-extensions")

# Use webdriver-manager to auto-download chromedriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Open Terabox login page
    driver.get("https://www.terabox.com")
    time.sleep(3)  # Wait for page load

    # Find and fill email & password
    email_input = driver.find_element(By.NAME, "username")  # Adjust selector if needed
    password_input = driver.find_element(By.NAME, "password")  # Adjust if different

    email_input.send_keys(TERABOX_EMAIL)
    password_input.send_keys(TERABOX_PASSWORD)

    # Click login button
    login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
    login_button.click()
    time.sleep(5)  # Wait for login

    # Check if login was successful
    try:
        profile_element = driver.find_element(By.CLASS_NAME, "user-profile")  # Adjust selector
        print("✅ Login successful!")
    except NoSuchElementException:
        print("❌ Login failed. Check credentials or website structure.")

    # Get cookies (for session management, if needed)
    cookies = driver.get_cookies()
    print("\n🔒 Session Cookies:")
    for cookie in cookies:
        print(f"{cookie['name']}: {cookie['value']}")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    driver.quit()  # Close browser
