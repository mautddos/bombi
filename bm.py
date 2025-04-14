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
        self.device_id = f"android-{str(uuid.uuid4())[:16]}"
        
    def generate_user_agent(self):
        android_version = random.randint(9, 13)
        device_model = f"{''.join(random.choices(string.ascii_uppercase, k=3))}{random.randint(111, 999)}"
        chrome_version = f"{random.randint(100, 115)}.0.0.0"
        return f'Mozilla/5.0 (Linux; Android {android_version}; {device_model}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Mobile Safari/537.36'

    def get_headers(self, country='US', language='en'):
        for _ in range(3):
            try:
                # Initial headers to get cookies
                temp_headers = {
                    'user-agent': self.user_agent,
                    'accept-language': f'{language}-{country},en;q=0.9',
                }
                
                self.session.headers.update(temp_headers)
                response = self.session.get(
                    'https://www.instagram.com/accounts/emailsignup/',
                    timeout=30
                )
                
                # Extract important cookies
                self.cookies = {
                    'csrftoken': response.cookies.get('csrftoken', str(uuid.uuid4()).replace('-', '')[:32]),
                    'mid': response.cookies.get('mid', str(uuid.uuid4()).upper()),
                    'ig_did': response.cookies.get('ig_did', str(uuid.uuid4())),
                    'ig_nrcb': '1',
                }
                
                # Get Facebook cookies
                fb_response = self.session.get("https://www.facebook.com/", timeout=30)
                try:
                    js_datr = fb_response.text.split('["_js_datr","')[1].split('",')[0]
                    self.cookies['datr'] = js_datr
                except:
                    self.cookies['datr'] = str(uuid.uuid4()).replace('-', '')[:20]
                
                # Build final headers
                cookie_str = '; '.join(f'{k}={v}' for k, v in self.cookies.items())
                
                self.headers = {
                    'authority': 'www.instagram.com',
                    'accept': '*/*',
                    'accept-language': f'{language}-{country},en;q=0.9',
                    'content-type': 'application/x-www-form-urlencoded',
                    'cookie': cookie_str,
                    'origin': 'https://www.instagram.com',
                    'referer': 'https://www.instagram.com/accounts/emailsignup/',
                    'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99"',
                    'sec-ch-ua-mobile': '?1',
                    'sec-ch-ua-platform': '"Android"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': self.user_agent,
                    'x-asbd-id': '198387',
                    'x-csrftoken': self.cookies['csrftoken'],
                    'x-ig-app-id': '1217981644879628',  # Updated app ID
                    'x-ig-www-claim': '0',
                    'x-instagram-ajax': '1007616494',
                    'x-requested-with': 'XMLHttpRequest',
                }
                
                return self.headers
                
            except Exception as e:
                print(f"Header generation error: {str(e)}")
                time.sleep(2)
        
        return None

    def generate_random_name(self):
        first_names = ["Emma", "Liam", "Olivia", "Noah", "Ava", "William", "Sophia", "James", "Isabella", "Oliver"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def get_username_suggestions(self, name, email):
        for _ in range(3):
            try:
                headers = self.headers.copy()
                headers['referer'] = 'https://www.instagram.com/accounts/signup/email/'
                
                data = {
                    'email': email,
                    'name': name,
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/web/accounts/username_suggestions/',
                    headers=headers,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'suggestions' in data and data['suggestions']:
                        return random.choice(data['suggestions'])
                    return f"{name.lower().replace(' ', '')}{random.randint(100, 999)}"
                    
            except Exception as e:
                print(f"Username suggestion error: {str(e)}")
                time.sleep(2)
        
        return f"{name.lower().replace(' ', '')}{random.randint(100, 999)}"

    def send_verification_email(self, email):
        for _ in range(3):
            try:
                headers = self.headers.copy()
                headers['referer'] = 'https://www.instagram.com/accounts/emailsignup/'
                
                data = {
                    'device_id': self.device_id,
                    'email': email,
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/accounts/send_verify_email/',
                    headers=headers,
                    data=data,
                    timeout=30
                )
                
                return response.json()
                
            except Exception as e:
                print(f"Verification email error: {str(e)}")
                time.sleep(2)
        
        return {'status': 'fail', 'message': 'Failed to send verification email'}

    def verify_confirmation_code(self, email, code):
        for _ in range(3):
            try:
                headers = self.headers.copy()
                headers['referer'] = 'https://www.instagram.com/accounts/signup/email_confirmation/'
                
                data = {
                    'code': code,
                    'device_id': self.device_id,
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
                print(f"Verification code error: {str(e)}")
                time.sleep(2)
        
        return {'status': 'fail', 'message': 'Failed to verify confirmation code'}

    def create_account(self, email, signup_code):
        for _ in range(3):
            try:
                name = self.generate_random_name()
                username = self.get_username_suggestions(name, email)
                password = f"{name.split()[0].strip()}@{random.randint(1000, 9999)}"
                
                headers = self.headers.copy()
                headers['referer'] = 'https://www.instagram.com/accounts/signup/email/'
                
                data = {
                    'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}',
                    'email': email,
                    'username': username,
                    'first_name': name,
                    'month': str(random.randint(1, 12)),
                    'day': str(random.randint(1, 28)),
                    'year': str(random.randint(1990, 2001)),
                    'client_id': self.device_id,
                    'seamless_login_enabled': '1',
                    'opt_into_one_tap': 'false',
                    'tos_version': 'eu',
                    'force_sign_up_code': signup_code,
                }
                
                response = self.session.post(
                    'https://www.instagram.com/api/v1/web/accounts/web_create_ajax/',
                    headers=headers,
                    data=data,
                    timeout=30
                )
                
                result = response.json()
                print("Account creation response:", result)
                
                if result.get('account_created', False) or result.get('user_id'):
                    account_info = {
                        'username': username,
                        'password': password,
                        'email': email,
                        'creation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    return account_info
                else:
                    error_message = result.get('errors', {}).get('email', ['Unknown error'])[0]
                    print(f"Account creation failed: {error_message}")
                    
            except Exception as e:
                print(f"Account creation error: {str(e)}")
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
            if not headers:
                raise Exception("Failed to initialize Instagram session")
            
            # Send verification email
            send_result = creator.send_verification_email(message)
            
            if send_result.get('email_sent', False) or send_result.get('status') == 'ok':
                update.message.reply_text("📧 Verification email sent! Please check your inbox and send me the 6-digit verification code.")
                context.user_data['email'] = message
                context.user_data['creator'] = creator
            else:
                error_msg = send_result.get('message', 'Unknown error')
                update.message.reply_text(f"❌ Failed to send verification email: {error_msg}")
        except Exception as e:
            update.message.reply_text(f"❌ An error occurred: {str(e)}")
    elif message.isdigit() and len(message) == 6:  # Basic verification code check
        if 'email' in context.user_data and 'creator' in context.user_data:
            email = context.user_data['email']
            creator = context.user_data['creator']
            
            # Verify code
            verify_result = creator.verify_confirmation_code(email, message)
            
            if verify_result.get('status') == 'ok' and 'signup_code' in verify_result:
                signup_code = verify_result['signup_code']
                
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
                    update.message.reply_text("❌ Failed to create account. Instagram might have detected automated activity. Try again later with a different email.")
            else:
                error_msg = verify_result.get('message', 'Invalid verification code')
                update.message.reply_text(f"❌ Verification failed: {error_msg}")
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
