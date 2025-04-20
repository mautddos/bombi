import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

def get_user_credentials():
    """Prompt user to enter email and password securely."""
    print("\n🔐 Enter Terabox Login Credentials")
    email = input("📧 Email: ").strip()
    password = input("🔑 Password: ").strip()
    
    if not email or not password:
        raise ValueError("❌ Email and password cannot be empty!")
    return email, password

def setup_driver():
    """Configure Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-extensions")
    
    # Run in headless mode (no browser window)
    # chrome_options.add_argument("--headless")  # Uncomment if needed
    
    # Path to ChromeDriver (adjust if needed)
    service = Service(executable_path="chromedriver.exe")  # Windows
    # service = Service(executable_path="./chromedriver")  # Linux/Mac
    
    return webdriver.Chrome(service=service, options=chrome_options)

def terabox_login(driver, email, password):
    """Perform Terabox login and return session cookies."""
    try:
        driver.get("https://www.terabox.com")
        time.sleep(3)  # Wait for page load

        # Find email & password fields (adjust selectors if needed)
        email_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")

        email_input.send_keys(email)
        password_input.send_keys(password)

        # Click login button
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
        login_button.click()
        time.sleep(5)  # Wait for login

        # Check if login was successful
        try:
            profile_element = driver.find_element(By.CLASS_NAME, "user-profile")
            print("✅ Login successful!")
            return driver.get_cookies()  # Return session cookies
        except NoSuchElementException:
            print("❌ Login failed. Check credentials or website structure.")
            return None

    except Exception as e:
        print(f"❌ Error during login: {e}")
        return None

def main():
    print("\n🚀 Terabox Login Automation")
    print("=" * 30)
    
    # Get credentials from user
    email, password = get_user_credentials()
    
    # Initialize WebDriver
    driver = setup_driver()
    
    try:
        # Perform login
        cookies = terabox_login(driver, email, password)
        
        if cookies:
            print("\n🔒 Session Cookies (Do NOT share!):")
            for cookie in cookies:
                print(f"{cookie['name']}: {cookie['value']}")
    
    finally:
        driver.quit()  # Close browser

if __name__ == "__main__":
    main()
