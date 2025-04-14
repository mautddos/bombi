import os
import time
import uuid
import string
import random
import requests
import webbrowser
from colorama import init, Fore, Style
from datetime import datetime

# Initialize colorama
init()

# Check and install required modules
required_modules = {
    'termcolor': 'termcolor',
    'names': 'names',
    'requests': 'requests',
    'cfonts': 'python-cfonts',
    'pyfiglet': 'pyfiglet'
}

for module, package in required_modules.items():
    try:
        __import__(module)
    except ImportError:
        os.system(f'pip install {package}')

import termcolor
import names
from cfonts import render
import pyfiglet

# Configuration
PROXIES = None  # You can add proxies here if needed
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 2  # seconds
DEFAULT_APP_ID = '936619743392459'  # Fallback Instagram app ID

class InstagramAccountCreator:
    def __init__(self):
        self.session = requests.Session()
        self.session.proxies = PROXIES
        self.user_agent = self.generate_user_agent()
        self.headers = None
        self.cookies = None
        
    def generate_user_agent(self):
        """Generate a random mobile user agent"""
        android_version = random.randint(9, 13)
        device_model = f"{''.join(random.choices(string.ascii_uppercase, k=3))}{random.randint(111, 999)}"
        chrome_version = f"{random.randint(100, 115)}.0.0.0"
        return f'Mozilla/5.0 (Linux; Android {android_version}; {device_model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Mobile Safari/537.36'

    def get_headers(self, country='US', language='en'):
        """Get Instagram headers with necessary cookies"""
        for _ in range(MAX_RETRIES):
            try:
                # Initial request to get cookies with a generic user agent
                temp_headers = {
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                # Get Instagram cookies first
                self.session.headers.update(temp_headers)
                ig_response = self.session.get(
                    'https://www.instagram.com/api/v1/web/accounts/login/ajax/',
                    timeout=30
                )
                
                # Extract cookies
                self.cookies = {
                    'csrftoken': ig_response.cookies.get('csrftoken', ''),
                    'mid': ig_response.cookies.get('mid', ''),
                    'ig_nrcb': '1',
                    'ig_did': ig_response.cookies.get('ig_did', str(uuid.uuid4())),
                }
                
                # Now get Facebook datr cookie with mobile user agent
                self.session.headers.update({'user-agent': self.user_agent})
                fb_response = self.session.get(
                    "https://www.facebook.com/", 
                    timeout=30
                )
                
                # Try to get datr cookie from Facebook
                try:
                    js_datr = fb_response.text.split('["_js_datr","')[1].split('",')[0]
                    self.cookies['datr'] = js_datr
                except:
                    self.cookies['datr'] = str(uuid.uuid4()).replace('-', '')[:20]
                
                # Build cookie string
                cookie_str = '; '.join(f'{k}={v}' for k, v in self.cookies.items())
                
                # Get Instagram homepage to find app ID and rollout hash
                headers = {
                    'authority': 'www.instagram.com',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': f'{language}-{country},en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                    'cookie': cookie_str,
                    'user-agent': self.user_agent,
                }
                
                response = self.session.get('https://www.instagram.com/', headers=headers, timeout=30)
                
                # Try to extract app ID and rollout hash, use defaults if not found
                try:
                    appid = response.text.split('APP_ID":"')[1].split('"')[0]
                except:
                    appid = DEFAULT_APP_ID
                
                try:
                    rollout = response.text.split('rollout_hash":"')[1].split('"')[0]
                except:
                    rollout = '1'
                
                # Final headers
                self.headers = {
                    'authority': 'www.instagram.com',
                    'accept': '*/*',
                    'accept-language': f'{language}-{country},en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                    'content-type': 'application/x-www-form-urlencoded',
                    'cookie': cookie_str,
                    'origin': 'https://www.instagram.com',
                    'referer': 'https://www.instagram.com/accounts/signup/email/',
                    'sec-ch-prefers-color-scheme': 'light',
                    'sec-ch-ua': '"Chromium";v="111", "Not(A:Brand";v="8"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-platform': '"Android"',
                    'user-agent': self.user_agent,
                    'x-asbd-id': '198387',
                    'x-csrftoken': self.cookies['csrftoken'],
                    'x-ig-app-id': str(appid),
                    'x-ig-www-claim': '0',
                    'x-instagram-ajax': str(rollout),
                    'x-requested-with': 'XMLHttpRequest',
                    'x-web-device-id': self.cookies['ig_did'],
                }
                
                return self.headers
                
            except Exception as e:
                print(f"{Fore.YELLOW}Error getting headers: {e}{Style.RESET_ALL}")
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # If all attempts fail, try with minimal required headers
        print(f"{Fore.YELLOW}Warning: Using fallback headers{Style.RESET_ALL}")
        self.headers = {
            'authority': 'www.instagram.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'referer': 'https://www.instagram.com/accounts/signup/email/',
            'sec-ch-ua': '"Chromium";v="111", "Not(A:Brand";v="8"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'user-agent': self.user_agent,
            'x-asbd-id': '198387',
            'x-csrftoken': self.cookies.get('csrftoken', 'missing'),
            'x-ig-app-id': DEFAULT_APP_ID,
            'x-ig-www-claim': '0',
            'x-instagram-ajax': '1',
            'x-requested-with': 'XMLHttpRequest',
            'x-web-device-id': self.cookies.get('ig_did', str(uuid.uuid4())),
        }
        return self.headers

    def get_username_suggestions(self, name, email):
        """Get username suggestions from Instagram"""
        for _ in range(MAX_RETRIES):
            try:
                headers = self.headers.copy()
                headers['referer'] = 'https://www.instagram.com/accounts/signup/birthday/'
                
                data = {
                    'email': email,
                    'name': name + str(random.randint(1, 99)),
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/web/accounts/username_suggestions/',
                    headers=headers,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200 and 'suggestions' in response.json():
                    return random.choice(response.json()['suggestions'])
                else:
                    print(f"{Fore.YELLOW}Username suggestions error: {response.text}{Style.RESET_ALL}")
                    
            except Exception as e:
                print(f"{Fore.YELLOW}Error getting username suggestions: {e}{Style.RESET_ALL}")
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # If all attempts fail, generate a random username
        return f"{name.lower()}{random.randint(100, 999)}"

    def send_verification_email(self, email):
        """Send verification email to the provided address"""
        for _ in range(MAX_RETRIES):
            try:
                data = {
                    'device_id': self.cookies['mid'],
                    'email': email,
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/accounts/send_verify_email/',
                    headers=self.headers,
                    data=data,
                    timeout=30
                )
                
                return response.json()
                
            except Exception as e:
                print(f"{Fore.YELLOW}Error sending verification email: {e}{Style.RESET_ALL}")
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return {'status': 'fail', 'message': 'Failed to send verification email'}

    def verify_confirmation_code(self, email, code):
        """Verify the confirmation code received via email"""
        for _ in range(MAX_RETRIES):
            try:
                headers = self.headers.copy()
                headers['referer'] = 'https://www.instagram.com/accounts/signup/emailConfirmation/'
                
                data = {
                    'code': code,
                    'device_id': self.cookies['mid'],
                    'email': email,
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/accounts/check_confirmation_code/',
                    headers=headers,
                    data=data,
                    timeout=30
                )
                
                return response.json()
                
            except Exception as e:
                print(f"{Fore.YELLOW}Error verifying confirmation code: {e}{Style.RESET_ALL}")
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return {'status': 'fail', 'message': 'Failed to verify confirmation code'}

    def create_account(self, email, signup_code):
        """Create the Instagram account with the verified email"""
        for _ in range(MAX_RETRIES):
            try:
                firstname = names.get_first_name()
                username = self.get_username_suggestions(firstname, email)
                password = f"{firstname.strip()}@{random.randint(111, 999)}"
                
                headers = self.headers.copy()
                headers['referer'] = 'https://www.instagram.com/accounts/signup/username/'
                
                data = {
                    'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{round(time.time())}:{password}',
                    'email': email,
                    'username': username,
                    'first_name': firstname,
                    'month': random.randint(1, 12),
                    'day': random.randint(1, 28),
                    'year': random.randint(1990, 2001),
                    'client_id': self.cookies['mid'],
                    'seamless_login_enabled': '1',
                    'tos_version': 'row',
                    'force_sign_up_code': signup_code,
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/web/accounts/web_create_ajax/',
                    headers=headers,
                    data=data,
                    timeout=30
                )
                
                result = response.json()
                
                if result.get('account_created', False):
                    account_info = {
                        'username': username,
                        'password': password,
                        'email': email,
                        'cookies': dict(response.cookies),
                        'headers': self.headers,
                        'creation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    return account_info
                else:
                    print(f"{Fore.YELLOW}Account creation failed: {response.text}{Style.RESET_ALL}")
                    if 'errors' in result:
                        print(f"{Fore.RED}Error details: {result['errors']}{Style.RESET_ALL}")
                    
            except Exception as e:
                print(f"{Fore.RED}Error creating account: {e}{Style.RESET_ALL}")
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return None

def display_banner():
    """Display the tool banner"""
    fonts = ['small']
    colors = [Fore.GREEN]

    for font in fonts:
        f = pyfiglet.Figlet(font=font)
        for color in colors:
            output = f.renderText('INSTA CREATOR')
            print(color + output + Style.RESET_ALL)
        
    print(Fore.YELLOW + "~ Instagram Account Creator ~" + Style.RESET_ALL)
    print(Fore.YELLOW + "~ For educational purposes only ~" + Style.RESET_ALL)
    print(Fore.RED + "________________________________________________________" + Style.RESET_ALL)

def main():
    display_banner()
    
    # Open Telegram channel (optional)
    try:
        webbrowser.open('https://t.me/example_channel')
    except:
        pass
    
    creator = InstagramAccountCreator()
    
    try:
        # Get headers first
        print(Fore.CYAN + "[*] Initializing session..." + Style.RESET_ALL)
        headers = creator.get_headers()
        
        # Get email from user
        email = input(Fore.GREEN + "[?] Enter your email: " + Style.RESET_ALL).strip()
        
        # Send verification email
        print(Fore.CYAN + "[*] Sending verification email..." + Style.RESET_ALL)
        send_result = creator.send_verification_email(email)
        
        if send_result.get('email_sent', False):
            # Get verification code from user
            code = input(Fore.GREEN + "[?] Enter the verification code: " + Style.RESET_ALL).strip()
            
            # Verify code
            print(Fore.CYAN + "[*] Verifying code..." + Style.RESET_ALL)
            verify_result = creator.verify_confirmation_code(email, code)
            
            if verify_result.get('status') == 'ok':
                signup_code = verify_result.get('signup_code')
                
                # Create account
                print(Fore.CYAN + "[*] Creating account..." + Style.RESET_ALL)
                account_info = creator.create_account(email, signup_code)
                
                if account_info:
                    print(Fore.GREEN + "\n[+] Account created successfully!" + Style.RESET_ALL)
                    print(Fore.YELLOW + "="*50 + Style.RESET_ALL)
                    print(Fore.CYAN + f"Username: {account_info['username']}" + Style.RESET_ALL)
                    print(Fore.CYAN + f"Password: {account_info['password']}" + Style.RESET_ALL)
                    print(Fore.CYAN + f"Email: {account_info['email']}" + Style.RESET_ALL)
                    print(Fore.CYAN + f"Created at: {account_info['creation_time']}" + Style.RESET_ALL)
                    print(Fore.YELLOW + "="*50 + Style.RESET_ALL)
                    
                    # Save account info to file
                    try:
                        with open('instagram_accounts.txt', 'a') as f:
                            f.write(f"Username: {account_info['username']}\n")
                            f.write(f"Password: {account_info['password']}\n")
                            f.write(f"Email: {account_info['email']}\n")
                            f.write(f"Created at: {account_info['creation_time']}\n")
                            f.write("="*50 + "\n")
                        print(Fore.GREEN + "[+] Account details saved to instagram_accounts.txt" + Style.RESET_ALL)
                    except Exception as e:
                        print(Fore.YELLOW + f"[-] Could not save account details: {e}" + Style.RESET_ALL)
                else:
                    print(Fore.RED + "[-] Failed to create account" + Style.RESET_ALL)
            else:
                print(Fore.RED + f"[-] Verification failed: {verify_result.get('message', 'Unknown error')}" + Style.RESET_ALL)
        else:
            print(Fore.RED + f"[-] Failed to send verification email: {send_result.get('message', 'Unknown error')}" + Style.RESET_ALL)
    
    except KeyboardInterrupt:
        print(Fore.RED + "\n[!] Process interrupted by user" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[!] An error occurred: {e}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()
