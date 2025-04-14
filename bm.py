import os
import time
import uuid
import string
import random
import requests
import webbrowser
from colorama import init, Fore, Style
from datetime import datetime
import threading
import queue
import json
from concurrent.futures import ThreadPoolExecutor

# Initialize colorama
init()

# Check and install required modules
required_modules = {
    'termcolor': 'termcolor',
    'names': 'names',
    'requests': 'requests',
    'cfonts': 'python-cfonts',
    'pyfiglet': 'pyfiglet',
    'fake_useragent': 'fake-useragent'
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
from fake_useragent import UserAgent

# Configuration
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 2  # seconds
DEFAULT_APP_ID = '936619743392459'  # Fallback Instagram app ID
MAX_PROXY_USAGE = 5  # Max accounts per proxy before rotation
PROXY_TIMEOUT = 10  # seconds
PROXY_TEST_URL = "https://www.google.com"  # URL to test proxy connectivity
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
]

def display_banner():
    """Display the program banner"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.YELLOW + "="*60 + Style.RESET_ALL)
    banner = pyfiglet.figlet_format("Instagram Creator", font="slant")
    print(Fore.CYAN + banner + Style.RESET_ALL)
    print(Fore.YELLOW + "="*60 + Style.RESET_ALL)
    print(Fore.GREEN + "Instagram Account Creator Tool".center(60) + Style.RESET_ALL)
    print(Fore.YELLOW + "="*60 + Style.RESET_ALL)
    print("\n")

class ProxyManager:
    def __init__(self):
        self.proxy_list = []
        self.proxy_usage = {}
        self.lock = threading.Lock()
        self.last_refresh = 0
        self.proxy_refresh_interval = 3600  # Refresh every hour
        
    def fetch_proxies(self):
        """Fetch fresh proxies from multiple sources and validate them"""
        new_proxies = set()
        
        for url in PROXY_SOURCES:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    proxies = response.text.splitlines()
                    for proxy in proxies:
                        proxy = proxy.strip()
                        if proxy and ':' in proxy:
                            new_proxies.add(proxy)
            except Exception as e:
                print(f"{Fore.YELLOW}Failed to fetch proxies from {url}: {e}{Style.RESET_ALL}")
        
        # Validate proxies before adding them to the list
        valid_proxies = []
        print(f"{Fore.CYAN}[*] Validating {len(new_proxies)} proxies...{Style.RESET_ALL}")
        
        def validate_proxy(proxy):
            try:
                proxies = {
                    'http': f'http://{proxy}',
                    'https': f'http://{proxy}'
                }
                response = requests.get(PROXY_TEST_URL, proxies=proxies, timeout=PROXY_TIMEOUT)
                if response.status_code == 200:
                    return True
            except:
                return False
        
        # Validate proxies in parallel (simple threading approach)
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(validate_proxy, new_proxies))
        
        for proxy, is_valid in zip(new_proxies, results):
            if is_valid:
                valid_proxies.append(proxy)
        
        with self.lock:
            self.proxy_list = valid_proxies
            self.proxy_usage = {proxy: 0 for proxy in self.proxy_list}
            self.last_refresh = time.time()
            print(f"{Fore.GREEN}[+] Fetched {len(self.proxy_list)} valid proxies{Style.RESET_ALL}")
        
        return len(self.proxy_list)
    
    def get_proxy(self):
        """Get a random proxy with low usage count"""
        if not self.proxy_list or time.time() - self.last_refresh > self.proxy_refresh_interval:
            self.fetch_proxies()
            
        with self.lock:
            if not self.proxy_list:
                print(f"{Fore.RED}[-] No valid proxies available{Style.RESET_ALL}")
                return None
                
            # Sort proxies by usage count and get the least used ones
            sorted_proxies = sorted(self.proxy_usage.items(), key=lambda x: x[1])
            least_used = [p for p, count in sorted_proxies if count < MAX_PROXY_USAGE]
            
            if not least_used:
                # All proxies have reached max usage, refresh the list
                self.fetch_proxies()
                least_used = self.proxy_list
            
            proxy = random.choice(least_used)
            self.proxy_usage[proxy] += 1
            
            return {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
    
    def mark_proxy_failed(self, proxy):
        """Mark a proxy as failed (remove from list)"""
        proxy_str = proxy.replace('http://', '').replace('https://', '')
        with self.lock:
            if proxy_str in self.proxy_list:
                self.proxy_list.remove(proxy_str)
                if proxy_str in self.proxy_usage:
                    del self.proxy_usage[proxy_str]
                print(f"{Fore.RED}[-] Removed failed proxy: {proxy_str}{Style.RESET_ALL}")

class InstagramAccountCreator:
    def __init__(self, proxy_manager=None):
        self.session = requests.Session()
        self.proxy_manager = proxy_manager
        self.current_proxy = None
        self.user_agent = UserAgent().random
        self.headers = None
        self.cookies = None
        self.account_count = 0
        
    def rotate_proxy(self):
        """Rotate to a new proxy"""
        if self.proxy_manager:
            self.current_proxy = self.proxy_manager.get_proxy()
            if self.current_proxy:
                self.session.proxies = self.current_proxy
                print(f"{Fore.CYAN}[*] Using proxy: {self.current_proxy['http']}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}[-] No valid proxies available{Style.RESET_ALL}")
                return False
        return True
    
    def generate_user_agent(self):
        """Generate a random mobile user agent"""
        return UserAgent().random
    
    def validate_proxy(self):
        """Check if current proxy is working"""
        if not self.current_proxy:
            return True
            
        try:
            response = self.session.get(PROXY_TEST_URL, timeout=PROXY_TIMEOUT)
            return response.status_code == 200
        except:
            if self.proxy_manager:
                self.proxy_manager.mark_proxy_failed(self.current_proxy['http'])
            return False
    
    def get_headers(self, country='US', language='en'):
        """Get Instagram headers with necessary cookies"""
        for _ in range(MAX_RETRIES):
            try:
                # Rotate proxy if needed
                if self.proxy_manager and (self.account_count % 2 == 0 or not self.validate_proxy()):
                    if not self.rotate_proxy():
                        return None
                
                # Update user agent
                self.user_agent = self.generate_user_agent()
                
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
                if self.proxy_manager:
                    self.rotate_proxy()
        
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

    def send_verification_email(self, email):
        """Send verification email to the provided address"""
        for _ in range(MAX_RETRIES):
            try:
                if not self.headers:
                    self.get_headers()
                
                data = {
                    'email': email,
                    'username': '',
                    'first_name': '',
                    'opt_into_one_tap': 'false'
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/web/accounts/email_signup/',
                    headers=self.headers,
                    data=data,
                    timeout=30
                )
                
                result = response.json()
                
                if result.get('email_sent', False):
                    return {'status': 'ok', 'email_sent': True}
                else:
                    return {'status': 'error', 'message': result.get('message', 'Unknown error')}
                
            except Exception as e:
                print(f"{Fore.YELLOW}Error sending verification email: {e}{Style.RESET_ALL}")
                time.sleep(DELAY_BETWEEN_REQUESTS)
                if self.proxy_manager:
                    self.rotate_proxy()
        
        return {'status': 'error', 'message': 'Max retries reached'}

    def verify_confirmation_code(self, email, code):
        """Verify the confirmation code sent to email"""
        for _ in range(MAX_RETRIES):
            try:
                if not self.headers:
                    self.get_headers()
                
                data = {
                    'code': code,
                    'email': email
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/web/accounts/email_confirm/',
                    headers=self.headers,
                    data=data,
                    timeout=30
                )
                
                result = response.json()
                
                if result.get('status') == 'ok':
                    return result
                else:
                    return {'status': 'error', 'message': result.get('message', 'Unknown error')}
                
            except Exception as e:
                print(f"{Fore.YELLOW}Error verifying confirmation code: {e}{Style.RESET_ALL}")
                time.sleep(DELAY_BETWEEN_REQUESTS)
                if self.proxy_manager:
                    self.rotate_proxy()
        
        return {'status': 'error', 'message': 'Max retries reached'}

    def create_account(self, email, signup_code):
        """Create the Instagram account with generated details"""
        try:
            # Generate random account details
            first_name = names.get_first_name()
            last_name = names.get_last_name()
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(100, 999)}"
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            
            if not self.headers:
                self.get_headers()
            
            data = {
                'email': email,
                'username': username,
                'first_name': first_name,
                'opt_into_one_tap': 'false',
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}',
                'month': str(random.randint(1, 12)),
                'day': str(random.randint(1, 28)),
                'year': str(random.randint(1980, 2000)),
                'client_id': self.cookies.get('ig_did', str(uuid.uuid4())),
                'seamless_login_enabled': '1',
                'tos_version': 'eu',
                'force_sign_up_code': signup_code
            }
            
            response = self.session.post(
                'https://www.instagram.com/api/v1/web/accounts/web_create_ajax/',
                headers=self.headers,
                data=data,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('account_created', False):
                self.account_count += 1
                return {
                    'username': username,
                    'password': password,
                    'email': email,
                    'creation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'proxy': self.current_proxy
                }
            else:
                print(f"{Fore.RED}Account creation failed: {result.get('message', 'Unknown error')}{Style.RESET_ALL}")
                return None
                
        except Exception as e:
            print(f"{Fore.RED}Error creating account: {e}{Style.RESET_ALL}")
            return None

def main():
    display_banner()
    
    # Initialize proxy manager
    proxy_manager = ProxyManager()
    proxy_manager.fetch_proxies()
    
    # Open Telegram channel (optional)
    try:
        webbrowser.open('https://t.me/example_channel')
    except:
        pass
    
    while True:
        creator = InstagramAccountCreator(proxy_manager)
        
        try:
            # Get headers first
            print(Fore.CYAN + "[*] Initializing session..." + Style.RESET_ALL)
            headers = creator.get_headers()
            
            if not headers:
                print(Fore.RED + "[-] Failed to initialize session due to proxy issues" + Style.RESET_ALL)
                continue
                
            # Get email from user
            email = input(Fore.GREEN + "[?] Enter your email (or 'quit' to exit): " + Style.RESET_ALL).strip()
            
            if email.lower() == 'quit':
                break
                
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
                        if account_info.get('proxy'):
                            print(Fore.CYAN + f"Proxy used: {account_info['proxy']['http']}" + Style.RESET_ALL)
                        print(Fore.YELLOW + "="*50 + Style.RESET_ALL)
                        
                        # Save account info to file
                        try:
                            with open('instagram_accounts.txt', 'a') as f:
                                f.write(f"Username: {account_info['username']}\n")
                                f.write(f"Password: {account_info['password']}\n")
                                f.write(f"Email: {account_info['email']}\n")
                                f.write(f"Created at: {account_info['creation_time']}\n")
                                if account_info.get('proxy'):
                                    f.write(f"Proxy: {account_info['proxy']['http']}\n")
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
            break
        except Exception as e:
            print(Fore.RED + f"[!] An error occurred: {e}" + Style.RESET_ALL)
        
        # Ask if user wants to create another account
        choice = input(Fore.GREEN + "\n[?] Create another account? (y/n): " + Style.RESET_ALL).strip().lower()
        if choice != 'y':
            break

if __name__ == "__main__":
    main()
