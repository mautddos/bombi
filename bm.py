import os
import time
import uuid
import string
import random
import requests
from cfonts import render
import names
import termcolor
from bs4 import BeautifulSoup

# Configuration
PROXIES = None
MAX_RETRIES = 3
DELAY_BETWEEN_ATTEMPTS = 2

class InstagramAccountCreator:
    def __init__(self):
        self.session = requests.Session()
        self.session.proxies = PROXIES
        self.user_agent = self.generate_user_agent()
        self.headers = None

    def generate_user_agent(self):
        """Generate a random mobile user agent"""
        android_version = random.randint(9, 13)
        device_model = f"{''.join(random.choices(string.ascii_uppercase, k=3))}{random.randint(111, 999)}"
        chrome_version = random.randint(110, 115)
        return (f'Mozilla/5.0 (Linux; Android {android_version}; {device_model}) '
                f'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 '
                'Mobile Safari/537.36')

    def get_initial_cookies(self):
        """Get initial cookies from Instagram"""
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    'https://www.instagram.com/',
                    headers={'User-Agent': self.user_agent},
                    timeout=30
                )
                
                if not response.cookies:
                    raise Exception("No cookies received from Instagram")
                
                required_cookies = ['csrftoken', 'mid', 'ig_did']
                if all(cookie in response.cookies for cookie in required_cookies):
                    return {
                        'csrftoken': response.cookies['csrftoken'],
                        'mid': response.cookies['mid'],
                        'ig_did': response.cookies['ig_did']
                    }
                
            except Exception as e:
                print(f"Error getting initial cookies (attempt {attempt + 1}): {e}")
                time.sleep(DELAY_BETWEEN_ATTEMPTS)
        
        raise Exception("Failed to get initial cookies after multiple attempts")

    def get_app_id_and_rollout(self, cookies):
        """Get app ID and rollout hash from Instagram"""
        for attempt in range(MAX_RETRIES):
            try:
                headers = {
                    'authority': 'www.instagram.com',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,'
                              'image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': 'en-US,en;q=0.9',
                    'cookie': f'csrftoken={cookies["csrftoken"]}; mid={cookies["mid"]}; ig_did={cookies["ig_did"]}',
                    'sec-ch-ua': '"Chromium";v="111", "Not(A:Brand";v="8"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-platform': '"Android"',
                    'user-agent': self.user_agent,
                }

                response = self.session.get(
                    'https://www.instagram.com/',
                    headers=headers,
                    timeout=30
                )

                soup = BeautifulSoup(response.text, 'html.parser')
                script = soup.find('script', text=lambda t: t and 'APP_ID' in t)
                
                if script:
                    script_text = script.string
                    app_id = script_text.split('APP_ID":"')[1].split('"')[0]
                    rollout_hash = script_text.split('rollout_hash":"')[1].split('"')[0]
                    return app_id, rollout_hash
                
            except Exception as e:
                print(f"Error getting app ID (attempt {attempt + 1}): {e}")
                time.sleep(DELAY_BETWEEN_ATTEMPTS)
        
        # Fallback values if extraction fails
        return '936619743392459', '1'

    def generate_headers(self):
        """Generate complete Instagram headers"""
        for attempt in range(MAX_RETRIES):
            try:
                cookies = self.get_initial_cookies()
                app_id, rollout_hash = self.get_app_id_and_rollout(cookies)

                headers = {
                    'authority': 'www.instagram.com',
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9',
                    'content-type': 'application/x-www-form-urlencoded',
                    'cookie': f'csrftoken={cookies["csrftoken"]}; mid={cookies["mid"]}; ig_did={cookies["ig_did"]}',
                    'origin': 'https://www.instagram.com',
                    'referer': 'https://www.instagram.com/accounts/signup/email/',
                    'sec-ch-ua': '"Chromium";v="111", "Not(A:Brand";v="8"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-platform': '"Android"',
                    'user-agent': self.user_agent,
                    'x-asbd-id': '198387',
                    'x-csrftoken': cookies["csrftoken"],
                    'x-ig-app-id': app_id,
                    'x-ig-www-claim': '0',
                    'x-instagram-ajax': rollout_hash,
                    'x-requested-with': 'XMLHttpRequest',
                    'x-web-device-id': cookies["ig_did"],
                }

                return headers

            except Exception as e:
                print(f"Error generating headers (attempt {attempt + 1}): {e}")
                time.sleep(DELAY_BETWEEN_ATTEMPTS)
        
        raise Exception("Failed to generate headers after multiple attempts")

    def get_username_suggestions(self, name, email):
        """Get username suggestions from Instagram"""
        for attempt in range(MAX_RETRIES):
            try:
                data = {
                    'email': email,
                    'name': name + str(random.randint(1, 99)),
                }

                response = self.session.post(
                    'https://www.instagram.com/api/v1/web/accounts/username_suggestions/',
                    headers=self.headers,
                    data=data,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'ok' and result.get('suggestions'):
                        return random.choice(result['suggestions'])
                
                print(f"Username suggestion failed (attempt {attempt + 1}): {response.text}")
                
            except Exception as e:
                print(f"Error getting username (attempt {attempt + 1}): {e}")
            
            time.sleep(DELAY_BETWEEN_ATTEMPTS)
        
        # Fallback username generation
        return f"{name.lower()}{random.randint(100, 999)}"

    def send_verification_email(self, email):
        """Send verification code to email"""
        for attempt in range(MAX_RETRIES):
            try:
                data = {
                    'device_id': self.headers['cookie'].split('mid=')[1].split(';')[0],
                    'email': email,
                }

                response = self.session.post(
                    'https://www.instagram.com/api/v1/accounts/send_verify_email/',
                    headers=self.headers,
                    data=data,
                    timeout=30
                )

                if response.status_code == 200 and response.json().get('email_sent'):
                    return True
                
                print(f"Verification email failed (attempt {attempt + 1}): {response.text}")
                
            except Exception as e:
                print(f"Error sending verification (attempt {attempt + 1}): {e}")
            
            time.sleep(DELAY_BETWEEN_ATTEMPTS)
        
        return False

    def validate_verification_code(self, email, code):
        """Validate the verification code"""
        for attempt in range(MAX_RETRIES):
            try:
                data = {
                    'code': code,
                    'device_id': self.headers['cookie'].split('mid=')[1].split(';')[0],
                    'email': email,
                }

                response = self.session.post(
                    'https://www.instagram.com/api/v1/accounts/check_confirmation_code/',
                    headers=self.headers,
                    data=data,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('status') == 'ok' and result.get('signup_code'):
                        return result['signup_code']
                
                print(f"Validation failed (attempt {attempt + 1}): {response.text}")
                
            except Exception as e:
                print(f"Error validating code (attempt {attempt + 1}): {e}")
            
            time.sleep(DELAY_BETWEEN_ATTEMPTS)
        
        return None

    def create_account(self, email, signup_code):
        """Create Instagram account"""
        for attempt in range(MAX_RETRIES):
            try:
                firstname = names.get_first_name()
                username = self.get_username_suggestions(firstname, email)
                password = f"{firstname.strip()}@{random.randint(111, 999)}"
                
                current_time = round(time.time())
                data = {
                    'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{current_time}:{password}',
                    'email': email,
                    'username': username,
                    'first_name': firstname,
                    'month': random.randint(1, 12),
                    'day': random.randint(1, 28),
                    'year': random.randint(1990, 2001),
                    'client_id': self.headers['cookie'].split('mid=')[1].split(';')[0],
                    'seamless_login_enabled': '1',
                    'tos_version': 'row',
                    'force_sign_up_code': signup_code,
                }

                response = self.session.post(
                    'https://www.instagram.com/api/v1/web/accounts/web_create_ajax/',
                    headers=self.headers,
                    data=data,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('account_created'):
                        print('\n' + '='*50)
                        print(termcolor.colored('Account created successfully!', 'green'))
                        print('='*50)
                        print(f'Username: {username}')
                        print(f'Password: {password}')
                        print(f'Session ID: {response.cookies.get("sessionid", "N/A")}')
                        print('='*50 + '\n')
                        return True
                
                print(f"Account creation failed (attempt {attempt + 1}): {response.text}")
                
            except Exception as e:
                print(f"Error creating account (attempt {attempt + 1}): {e}")
            
            time.sleep(DELAY_BETWEEN_ATTEMPTS)
        
        return False

def display_banner():
    """Display the program banner"""
    os.system('cls' if os.name == 'nt' else 'clear')
    output = render('INSTA CREATOR', colors=['white', 'magenta'], align='center')
    print(output)
    print("      ~ Improved Instagram Account Creator ~")
    print(termcolor.colored("="*60, "magenta"))

def get_email_input():
    """Get and validate email input"""
    while True:
        email = input(termcolor.colored('\nEnter your email -> ', 'cyan')).strip()
        if '@' in email and '.' in email.split('@')[1]:
            return email
        print(termcolor.colored("Invalid email address! Please try again.", "red"))

def get_verification_code():
    """Get and validate verification code"""
    while True:
        code = input(termcolor.colored('\nEnter the verification code -> ', 'cyan')).strip()
        if code.isdigit() and len(code) == 6:
            return code
        print(termcolor.colored("Invalid code! Must be 6 digits. Please try again.", "red"))

def main():
    """Main program flow"""
    display_banner()
    
    try:
        creator = InstagramAccountCreator()
        
        # Step 1: Generate headers
        print(termcolor.colored("\n[1/4] Initializing session...", "yellow"))
        creator.headers = creator.generate_headers()
        print(termcolor.colored("Session initialized successfully!", "green"))
        
        # Step 2: Get email and send verification
        email = get_email_input()
        print(termcolor.colored("\n[2/4] Sending verification code...", "yellow"))
        if creator.send_verification_email(email):
            print(termcolor.colored("Verification code sent successfully!", "green"))
        else:
            print(termcolor.colored("Failed to send verification code.", "red"))
            return
        
        # Step 3: Validate code
        code = get_verification_code()
        print(termcolor.colored("\n[3/4] Validating code...", "yellow"))
        signup_code = creator.validate_verification_code(email, code)
        if signup_code:
            print(termcolor.colored("Code validated successfully!", "green"))
        else:
            print(termcolor.colored("Failed to validate code.", "red"))
            return
        
        # Step 4: Create account
        print(termcolor.colored("\n[4/4] Creating account...", "yellow"))
        if creator.create_account(email, signup_code):
            print(termcolor.colored("Account creation process completed!", "green"))
        else:
            print(termcolor.colored("Failed to create account.", "red"))
            
    except Exception as e:
        print(termcolor.colored(f"\nAn error occurred: {e}", "red"))
    finally:
        print(termcolor.colored("\nProcess completed.", "magenta"))

if __name__ == "__main__":
    main()
