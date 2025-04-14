import os
import time
import uuid
import string
import random
import requests
from datetime import datetime
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters

# Telegram Bot Token
TOKEN = "8102265512:AAGXrXgWir3LxkHlN8jruWTdXh7hOo8yasM"
CHANNEL_LINK = "https://t.me/+wiXRUCMeUfczYjE1"

# Initialize the bot
bot = Bot(token=TOKEN)

class InstagramAccountCreator:
    def __init__(self):
        self.session = requests.Session()
        self.user_agent = self.generate_user_agent()
        self.headers = None
        self.cookies = None
        
    def generate_user_agent(self):
        android_version = random.randint(9, 13)
        device_model = f"{''.join(random.choices(string.ascii_uppercase, k=3))}{random.randint(111, 999)}"
        chrome_version = f"{random.randint(100, 115)}.0.0.0"
        return f'Mozilla/5.0 (Linux; Android {android_version}; {device_model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Mobile Safari/537.36'

    def get_headers(self, country='US', language='en'):
        for _ in range(3):
            try:
                temp_headers = {
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                self.session.headers.update(temp_headers)
                ig_response = self.session.get(
                    'https://www.instagram.com/api/v1/web/accounts/login/ajax/',
                    timeout=30
                )
                
                self.cookies = {
                    'csrftoken': ig_response.cookies.get('csrftoken', ''),
                    'mid': ig_response.cookies.get('mid', ''),
                    'ig_nrcb': '1',
                    'ig_did': ig_response.cookies.get('ig_did', str(uuid.uuid4())),
                }
                
                self.session.headers.update({'user-agent': self.user_agent})
                fb_response = self.session.get("https://www.facebook.com/", timeout=30)
                
                try:
                    js_datr = fb_response.text.split('["_js_datr","')[1].split('",')[0]
                    self.cookies['datr'] = js_datr
                except:
                    self.cookies['datr'] = str(uuid.uuid4()).replace('-', '')[:20]
                
                cookie_str = '; '.join(f'{k}={v}' for k, v in self.cookies.items())
                
                headers = {
                    'authority': 'www.instagram.com',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': f'{language}-{country},en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                    'cookie': cookie_str,
                    'user-agent': self.user_agent,
                }
                
                response = self.session.get('https://www.instagram.com/', headers=headers, timeout=30)
                
                try:
                    appid = response.text.split('APP_ID":"')[1].split('"')[0]
                except:
                    appid = '936619743392459'
                
                try:
                    rollout = response.text.split('rollout_hash":"')[1].split('"')[0]
                except:
                    rollout = '1'
                
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
                time.sleep(2)
        
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
            'x-ig-app-id': '936619743392459',
            'x-ig-www-claim': '0',
            'x-instagram-ajax': '1',
            'x-requested-with': 'XMLHttpRequest',
            'x-web-device-id': self.cookies.get('ig_did', str(uuid.uuid4())),
        }
        return self.headers

    def get_username_suggestions(self, name, email):
        for _ in range(3):
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
                    
            except Exception:
                time.sleep(2)
        
        return f"{name.lower()}{random.randint(100, 999)}"

    def send_verification_email(self, email):
        for _ in range(3):
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
                
            except Exception:
                time.sleep(2)
        
        return {'status': 'fail', 'message': 'Failed to send verification email'}

    def verify_confirmation_code(self, email, code):
        for _ in range(3):
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
                
            except Exception:
                time.sleep(2)
        
        return {'status': 'fail', 'message': 'Failed to verify confirmation code'}

    def create_account(self, email, signup_code):
        for _ in range(3):
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
                        'creation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    return account_info
                    
            except Exception:
                time.sleep(2)
        
        return None

def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the command /start is issued."""
    welcome_message = """
🌟 *Welcome to Instagram Account Creator Bot* 🌟

This bot helps you create Instagram accounts easily. 

🔹 *Features:*
- Create Instagram accounts with email verification
- Generate random usernames and passwords
- Simple and easy to use

📢 *Join our channel for updates and more tools:*
"""

    keyboard = [
        [InlineKeyboardButton("Join Our Channel 📢", url=CHANNEL_LINK)],
        [InlineKeyboardButton("Create Account 🚀", callback_data='create_account')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        welcome_message, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

def button(update: Update, context: CallbackContext) -> None:
    """Handle button presses."""
    query = update.callback_query
    query.answer()

    if query.data == 'create_account':
        query.edit_message_text(text="Please send me the email address you want to use for the Instagram account.")

def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle regular messages."""
    message = update.message.text
    
    if '@' in message:  # Basic email check
        update.message.reply_text("🔄 Processing your request...")
        
        creator = InstagramAccountCreator()
        
        try:
            # Get headers
            headers = creator.get_headers()
            
            # Send verification email
            send_result = creator.send_verification_email(message)
            
            if send_result.get('email_sent', False):
                update.message.reply_text("📧 Verification email sent! Please check your inbox and send me the verification code.")
                context.user_data['email'] = message
                context.user_data['creator'] = creator
            else:
                update.message.reply_text("❌ Failed to send verification email. Please try again later.")
        except Exception as e:
            update.message.reply_text(f"❌ An error occurred: {str(e)}")
    elif message.isdigit() and len(message) == 6:  # Basic verification code check
        if 'email' in context.user_data and 'creator' in context.user_data:
            email = context.user_data['email']
            creator = context.user_data['creator']
            
            # Verify code
            verify_result = creator.verify_confirmation_code(email, message)
            
            if verify_result.get('status') == 'ok':
                signup_code = verify_result.get('signup_code')
                
                # Create account
                account_info = creator.create_account(email, signup_code)
                
                if account_info:
                    success_message = f"""
✅ *Account created successfully!*

📝 *Account Details:*
👤 Username: `{account_info['username']}`
🔑 Password: `{account_info['password']}`
📧 Email: `{account_info['email']}`
⏰ Created at: `{account_info['creation_time']}`

🔒 *Please keep your credentials safe!*
"""
                    update.message.reply_text(success_message, parse_mode='Markdown')
                else:
                    update.message.reply_text("❌ Failed to create account. Please try again.")
            else:
                update.message.reply_text(f"❌ Verification failed: {verify_result.get('message', 'Unknown error')}")
        else:
            update.message.reply_text("❌ No email verification in progress. Please start over with /start")
    else:
        update.message.reply_text("Please use /start to begin or send a valid email address.")

def main() -> None:
    """Start the bot."""
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
