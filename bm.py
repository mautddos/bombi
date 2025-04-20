import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# 1. Enter your credentials manually
TERABOX_EMAIL = "combill925@gmail.com"
TERABOX_PASSWORD = "www.chut.com"

# 2. Setup Chrome Options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run without GUI
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# 3. Install and use proper chromedriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # 4. Go to Terabox website
    driver.get("https://www.terabox.com")
    time.sleep(3)  # Wait for page load

    # 5. Login process
    email_input = driver.find_element(By.NAME, "username")  # Check if selector is correct
    password_input = driver.find_element(By.NAME, "password")
    email_input.send_keys(TERABOX_EMAIL)
    password_input.send_keys(TERABOX_PASSWORD)

    # Click login button
    login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
    login_button.click()
    time.sleep(5)

    # 6. Confirm login
    try:
        profile_element = driver.find_element(By.CLASS_NAME, "user-profile")
        print("✅ Login successful!")
    except NoSuchElementException:
        print("❌ Login failed. Check credentials or site structure.")

    # 7. Print session cookies
    cookies = driver.get_cookies()
    print("\n🔒 Session Cookies:")
    for cookie in cookies:
        print(f"{cookie['name']}: {cookie['value']}")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    driver.quit()
