import os
import time
import random
import string
import requests
from cfonts import render
import names
import termcolor
import json

# Configuration
PROXIES = None
MAX_RETRIES = 3
DELAY_BETWEEN_ATTEMPTS = 3
DEFAULT_APP_ID = '936619743392459'
DEFAULT_ROLLOUT_HASH = '1'

class InstagramAccountCreator:
    def __init__(self):
        self.session = requests.Session()
        self.session.proxies = PROXIES
        self.user_agent = self._generate_user_agent()
        self.headers = None
        self.cookies = {}

    def _generate_user_agent(self):
        """Generate a random mobile user agent"""
        android_version = random.randint(9, 13)
        device_model = f"{''.join(random.choices(string.ascii_uppercase, k=3))}{random.randint(111, 999)}"
        chrome_version = random.randint(110, 115)
        return (f'Mozilla/5.0 (Linux; Android {android_version}; {device_model}) '
                f'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 '
                'Mobile Safari/537.36')

    def _get_initial_cookies(self):
        """Get initial cookies from Instagram with multiple fallback methods"""
        for attempt in range(MAX_RETRIES):
            try:
                # Try direct API endpoint first
                response = self.session.get(
                    'https://www.instagram.com/data/shared_data/',
                    headers={'User-Agent': self.user_agent},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'config' in data and 'csrf_token' in data['config']:
                        self.cookies.update({
                            'csrftoken': data['config']['csrf_token'],
                            'mid': data['config'].get('mid', str(uuid.uuid4())),
                            'ig_did': data['config'].get('ig_did', str(uuid.uuid4()))
                        })
                        return True
                
                # Fallback to main page if API endpoint fails
                response = self.session.get(
                    'https://www.instagram.com/',
                    headers={'User-Agent': self.user_agent},
                    timeout=30
                )
                
                # Extract cookies from response
                if response.cookies:
                    required_cookies = ['csrftoken', 'mid', 'ig_did']
                    for cookie in required_cookies:
                        if cookie in response.cookies:
                            self.cookies[cookie] = response.cookies[cookie]
                    
                    # Generate missing cookies if needed
                    if 'mid' not in self.cookies:
                        self.cookies['mid'] = str(uuid.uuid4())
                    if 'ig_did' not in self.cookies:
                        self.cookies['ig_did'] = str(uuid.uuid4())
                    
                    return True
                
            except Exception as e:
                print(f"Cookie fetch error (attempt {attempt + 1}): {str(e)}")
                time.sleep(DELAY_BETWEEN_ATTEMPTS)
        
        return False

    def _get_app_id_and_rollout(self):
        """Get app ID and rollout hash with fallback to defaults"""
        try:
            response = self.session.get(
                'https://www.instagram.com/data/shared_data/',
                headers={'User-Agent': self.user_agent},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                app_id = data.get('config', {}).get('app_id', DEFAULT_APP_ID)
                rollout_hash = data.get('config', {}).get('rollout_hash', DEFAULT_ROLLOUT_HASH)
                return app_id, rollout_hash
                
        except Exception as e:
            print(f"Error getting app ID: {str(e)}")
        
        return DEFAULT_APP_ID, DEFAULT_ROLLOUT_HASH

    def generate_headers(self):
        """Generate complete Instagram headers with robust fallbacks"""
        for attempt in range(MAX_RETRIES):
            try:
                if not self._get_initial_cookies():
                    raise Exception("Could not get required cookies")
                
                app_id, rollout_hash = self._get_app_id_and_rollout()
                
                headers = {
                    'authority': 'www.instagram.com',
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9',
                    'content-type': 'application/x-www-form-urlencoded',
                    'cookie': f'csrftoken={self.cookies["csrftoken"]}; mid={self.cookies["mid"]}; ig_did={self.cookies["ig_did"]}',
                    'origin': 'https://www.instagram.com',
                    'referer': 'https://www.instagram.com/accounts/signup/email/',
                    'sec-ch-ua': '"Chromium";v="111", "Not(A:Brand";v="8"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-platform': '"Android"',
                    'user-agent': self.user_agent,
                    'x-asbd-id': '198387',
                    'x-csrftoken': self.cookies["csrftoken"],
                    'x-ig-app-id': app_id,
                    'x-ig-www-claim': '0',
                    'x-instagram-ajax': rollout_hash,
                    'x-requested-with': 'XMLHttpRequest',
                    'x-web-device-id': self.cookies["ig_did"],
                }

                # Test headers with a simple request
                test_response = self.session.get(
                    'https://www.instagram.com/api/v1/web/accounts/login/ajax/',
                    headers=headers,
                    timeout=30
                )
                
                if test_response.status_code == 200:
                    self.headers = headers
                    return True
                
                print(f"Header test failed (status {test_response.status_code})")
                
            except Exception as e:
                print(f"Header generation error (attempt {attempt + 1}): {str(e)}")
                time.sleep(DELAY_BETWEEN_ATTEMPTS)
        
        raise Exception("Failed to generate valid headers after multiple attempts")

    # [Rest of the methods remain the same as in the previous version]
    # get_username_suggestions(), send_verification_email(), 
    # validate_verification_code(), create_account() methods go here...

def main():
    """Main program flow"""
    try:
        creator = InstagramAccountCreator()
        
        print(termcolor.colored("\n[1/4] Initializing session...", "yellow"))
        if creator.generate_headers():
            print(termcolor.colored("Session initialized successfully!", "green"))
        else:
            print(termcolor.colored("Failed to initialize session", "red"))
            return
        
        # [Rest of the main flow remains the same]
        # Continue with email input, verification, and account creation...
        
    except Exception as e:
        print(termcolor.colored(f"\nFatal error: {str(e)}", "red"))
    finally:
        print(termcolor.colored("\nProcess completed.", "magenta"))

if __name__ == "__main__":
    display_banner()
    main()
