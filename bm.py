import os
import time
import uuid
import string
import random
import requests
import webbrowser
from cfonts import render
import names
import termcolor

# Open Telegram channel
proxies = None

def get_headers(country, language):
    """Generate Instagram headers with proper cookies and tokens"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Generate random user agent
            android_version = random.randint(9, 13)
            device_model = f"{''.join(random.choices(string.ascii_uppercase, k=3))}{random.randint(111, 999)}"
            chrome_version = random.randint(110, 115)
            an_agent = (f'Mozilla/5.0 (Linux; Android {android_version}; {device_model}) '
                       f'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 '
                       'Mobile Safari/537.36')

            # Get initial cookies from Facebook
            fb_response = requests.get(
                "https://www.facebook.com/",
                headers={'user-agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 '
                        '(KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'},
                proxies=proxies,
                timeout=30
            )
            
            # Extract _js_datr cookie more reliably
            js_datr = None
            if '_js_datr' in fb_response.cookies:
                js_datr = fb_response.cookies['_js_datr']
            else:
                for cookie in fb_response.headers.get('Set-Cookie', '').split(';'):
                    if '_js_datr=' in cookie:
                        js_datr = cookie.split('_js_datr=')[1].split(';')[0]
                        break
            
            if not js_datr:
                raise Exception("Could not extract _js_datr cookie from Facebook response")

            # Get Instagram cookies
            ig_response = requests.get(
                'https://www.instagram.com/api/v1/web/accounts/login/ajax/',
                headers={'user-agent': an_agent},
                proxies=proxies,
                timeout=30
            )
            
            if not ig_response.cookies:
                raise Exception("No cookies received from Instagram")
                
            r = ig_response.cookies

            # First headers request to get app ID
            headers1 = {
                'authority': 'www.instagram.com',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,'
                         'image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': f'{language}-{country},en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                'cookie': f'dpr=3; csrftoken={r["csrftoken"]}; mid={r["mid"]}; ig_nrcb=1; '
                         f'ig_did={r["ig_did"]}; datr={js_datr}',
                'sec-ch-prefers-color-scheme': 'light',
                'sec-ch-ua': '"Chromium";v="111", "Not(A:Brand";v="8"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': an_agent,
                'viewport-width': '980',
            }

            response1 = requests.get(
                'https://www.instagram.com/',
                headers=headers1,
                proxies=proxies,
                timeout=30
            )

            # Extract required IDs from response with fallback values
            try:
                appid = response1.text.split('APP_ID":"')[1].split('"')[0]
            except (IndexError, KeyError):
                appid = '936619743392459'  # fallback app ID
            
            try:
                rollout = response1.text.split('rollout_hash":"')[1].split('"')[0]
            except (IndexError, KeyError):
                rollout = '1'  # fallback rollout hash

            # Final headers with all required parameters
            headers = {
                'authority': 'www.instagram.com',
                'accept': '*/*',
                'accept-language': f'{language}-{country},en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                'content-type': 'application/x-www-form-urlencoded',
                'cookie': f'dpr=3; csrftoken={r["csrftoken"]}; mid={r["mid"]}; ig_nrcb=1; '
                          f'ig_did={r["ig_did"]}; datr={js_datr}',
                'origin': 'https://www.instagram.com',
                'referer': 'https://www.instagram.com/accounts/signup/email/',
                'sec-ch-prefers-color-scheme': 'light',
                'sec-ch-ua': '"Chromium";v="111", "Not(A:Brand";v="8"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': an_agent,
                'viewport-width': '360',
                'x-asbd-id': '198387',
                'x-csrftoken': r["csrftoken"],
                'x-ig-app-id': str(appid),
                'x-ig-www-claim': '0',
                'x-instagram-ajax': str(rollout),
                'x-requested-with': 'XMLHttpRequest',
                'x-web-device-id': r["ig_did"],
            }

            return headers

        except Exception as e:
            print(f"Error getting headers (attempt {attempt + 1}/{max_retries}): {str(e)}")
            time.sleep(2)
    
    raise Exception("Failed to get headers after multiple attempts")

def get_username(headers, name, email):
    """Get username suggestions from Instagram"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            updict = {"referer": 'https://www.instagram.com/accounts/signup/birthday/'}
            headers = {key: updict.get(key, headers[key]) for key in headers}

            data = {
                'email': email,
                'name': name + str(random.randint(1, 99)),
            }

            response = requests.post(
                'https://www.instagram.com/api/v1/web/accounts/username_suggestions/',
                headers=headers,
                data=data,
                proxies=proxies,
                timeout=30
            )

            if response.status_code == 200 and 'status":"ok' in response.text:
                suggestions = response.json().get('suggestions', [])
                if suggestions:
                    return random.choice(suggestions)
                else:
                    # Fallback username generation if no suggestions
                    return f"{name.lower()}{random.randint(100, 999)}"
            else:
                print(f"Username suggestion failed (attempt {attempt + 1}): {response.text}")
                time.sleep(1)

        except Exception as e:
            print(f"Error getting username (attempt {attempt + 1}): {e}")
            time.sleep(2)
    
    # Final fallback if all attempts fail
    return f"{name.lower()}{random.randint(1000, 9999)}"

def send_sms(headers, email):
    """Send verification code to email"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            data = {
                'device_id': headers['cookie'].split('mid=')[1].split(';')[0],
                'email': email,
            }

            response = requests.post(
                'https://www.instagram.com/api/v1/accounts/send_verify_email/',
                headers=headers,
                data=data,
                proxies=proxies,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"Send SMS failed (attempt {attempt + 1}): {response.text}")
                time.sleep(1)
                
        except Exception as e:
            print(f"Error sending SMS (attempt {attempt + 1}): {e}")
            time.sleep(2)
    
    return None

def validate_code(headers, email, code):
    """Validate the verification code"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            updict = {"referer": 'https://www.instagram.com/accounts/signup/emailConfirmation/'}
            headers = {key: updict.get(key, headers[key]) for key in headers}

            data = {
                'code': code,
                'device_id': headers['cookie'].split('mid=')[1].split(';')[0],
                'email': email,
            }

            response = requests.post(
                'https://www.instagram.com/api/v1/accounts/check_confirmation_code/',
                headers=headers,
                data=data,
                proxies=proxies,
                timeout=30
            )
            
            if response.status_code == 200:
                return response
            else:
                print(f"Validation failed (attempt {attempt + 1}): {response.text}")
                time.sleep(1)
                
        except Exception as e:
            print(f"Error validating code (attempt {attempt + 1}): {e}")
            time.sleep(2)
    
    return None

def create_account(headers, email, signup_code):
    """Create Instagram account"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            firstname = names.get_first_name()
            username = get_username(headers, firstname, email)
            password = firstname.strip() + '@' + str(random.randint(111, 999))

            updict = {"referer": 'https://www.instagram.com/accounts/signup/username/'}
            headers = {key: updict.get(key, headers[key]) for key in headers}
            
            current_time = round(time.time())
            data = {
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{current_time}:{password}',
                'email': email,
                'username': username,
                'first_name': firstname,
                'month': random.randint(1, 12),
                'day': random.randint(1, 28),
                'year': random.randint(1990, 2001),
                'client_id': headers['cookie'].split('mid=')[1].split(';')[0],
                'seamless_login_enabled': '1',
                'tos_version': 'row',
                'force_sign_up_code': signup_code,
            }

            response = requests.post(
                'https://www.instagram.com/api/v1/web/accounts/web_create_ajax/',
                headers=headers,
                data=data,
                proxies=proxies,
                timeout=30
            )

            if response.status_code == 200 and '"account_created":true' in response.text:
                print('\n' + '='*50)
                print(termcolor.colored('Account created successfully!', 'green'))
                print('='*50)
                print(f'Username: {username}')
                print(f'Password: {password}')
                print(f'Sessionid: {response.cookies.get("sessionid", "N/A")}')
                print(f'Csrftoken: {response.cookies.get("csrftoken", "N/A")}')
                print(f'Ds_user_id: {response.cookies.get("ds_user_id", "N/A")}')
                print(f'Ig_did: {response.cookies.get("ig_did", "N/A")}')
                print(f'Rur: {response.cookies.get("rur", "N/A")}')
                print(f'Mid: {headers["cookie"].split("mid=")[1].split(";")[0]}')
                print(f'Datr: {headers["cookie"].split("datr=")[1] if "datr=" in headers["cookie"] else "N/A"}')
                print('='*50 + '\n')
                return True
            else:
                print(f"Account creation failed (attempt {attempt + 1}): {response.text}")
                time.sleep(1)

        except Exception as e:
            print(f"Error creating account (attempt {attempt + 1}): {e}")
            time.sleep(2)
    
    return False

def main():
    """Main function to run the account creation process"""
    # Display banner
    output = render('MODCA', colors=['white', 'magenta'], align='center')
    print(output)
    print("      ~ Programmer • Modca • -> @B_6_Q ~ Channel: @ModcaTheLost ~")
    print(termcolor.colored("_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _", "white"))
    
    try:
        # Get headers
        print(termcolor.colored("\nInitializing headers...", "yellow"))
        headers = get_headers(country='US', language='en')
        
        # Get email input
        email = input(termcolor.colored('\nEnter your email -> ', 'cyan'))
        if not email or '@' not in email:
            print(termcolor.colored("Invalid email address!", "red"))
            return
        
        print(termcolor.colored("—" * 60, "magenta"))
        
        # Send verification code
        print(termcolor.colored("\nSending verification code...", "yellow"))
        sms_response = send_sms(headers, email)
        if sms_response and 'email_sent":true' in sms_response:
            print(termcolor.colored("Verification code sent successfully!", "green"))
            print(termcolor.colored("—" * 60, "magenta"))
            
            # Get verification code input
            code = input(termcolor.colored('\nEnter the verification code -> ', 'cyan'))
            if not code or not code.isdigit():
                print(termcolor.colored("Invalid verification code!", "red"))
                return
            
            print(termcolor.colored("—" * 60, "magenta"))
            
            # Validate code
            print(termcolor.colored("\nValidating code...", "yellow"))
            validation_response = validate_code(headers, email, code)
            if validation_response and 'status":"ok' in validation_response.text:
                signup_code = validation_response.json().get('signup_code')
                if not signup_code:
                    print(termcolor.colored("Could not get signup code from response!", "red"))
                    return
                
                print(termcolor.colored("Code validated successfully!", "green"))
                print(termcolor.colored("—" * 60, "magenta"))
                
                # Create account
                print(termcolor.colored("\nCreating account...", "yellow"))
                if create_account(headers, email, signup_code):
                    print(termcolor.colored("Account creation process completed!", "green"))
                else:
                    print(termcolor.colored("Failed to create account after multiple attempts.", "red"))
            else:
                print(termcolor.colored("Invalid verification code or validation failed.", "red"))
        else:
            print(termcolor.colored("Failed to send verification code.", "red"))
            
    except Exception as e:
        print(termcolor.colored(f"\nAn error occurred: {e}", "red"))
    finally:
        print(termcolor.colored("\nProcess completed.", "magenta"))

if __name__ == "__main__":
    main()
