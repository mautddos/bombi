import random
import logging
import requests
import time
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from secrets import token_hex
from user_agent import generate_user_agent

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TOKEN = "7987107314:AAFFNznZhy9GH0CRkgB0MsKhhB1TY_mQb8Q"
CHANNEL_LINK = "https://t.me/+wiXRUCMeUfczYjE1"
ADMIN_ID = "8167507955"  # Your Telegram user ID for error notifications
REQUEST_TIMEOUT = 10  # seconds
MAX_WORKERS = 5  # For thread pool

class InstagramChecker:
    def __init__(self):
        self.available_count = 0
        self.unavailable_count = 0
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        
    def generate_username(self, pattern):
        """Generate username based on pattern"""
        All = "qwertyuiopasdfghjklzxcvbnm"
        Num = "0123456789"
        
        username = ''
        i = 0 
        while i < len(pattern):
            if pattern[i] == '#':
                username += random.choice(All + Num)  
            elif pattern[i] == '*':
                username += random.choice(All)  
            elif pattern[i] == '"':
                username += random.choice(Num)
            elif pattern[i] == '_':
                username += '_'  
            elif pattern[i] == '.':
                username += '.'  
            elif pattern[i:i+2] == '@@':
                username += random.choice(All) * 2 
                i += 1
            elif pattern[i:i+2] == '§§':
                username += random.choice(Num) * 2  
                i += 1  
            else:
                username += pattern[i]
            i += 1  
        return username.lower()

    def check_instagram(self, username):
        """Check if username is available on Instagram using multiple methods"""
        try:
            # First try the direct profile check
            result = self.profile_check(username)
            if result is not None:
                return result
                
            # If unclear, try the API check
            result = self.api_check(username)
            if result is not None:
                return result
                
            # If still unclear, try the signup check
            return self.signup_check(username)
            
        except Exception as e:
            logger.error(f"Error checking username {username}: {str(e)}")
            return None

    def profile_check(self, username):
        """Check username availability by visiting profile page"""
        try:
            headers = {
                'User-Agent': generate_user_agent(),
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            response = requests.get(
                f'https://www.instagram.com/{username}/',
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 404:
                return True  # Available
            elif response.status_code == 200:
                return False  # Taken
            return None
            
        except Exception as e:
            logger.error(f"Profile check failed for {username}: {str(e)}")
            return None

    def api_check(self, username):
        """Check username availability through Instagram API"""
        try:
            csr = token_hex(8) * 2
            headers = {
                'authority': 'www.instagram.com',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://www.instagram.com',
                'referer': f'https://www.instagram.com/{username}/',
                'user-agent': generate_user_agent(),
                'x-csrftoken': csr,
                'x-ig-app-id': '936619743392459',
            }

            response = requests.get(
                f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}',
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 404:
                return True  # Available
            elif response.status_code == 200:
                return False  # Taken
            return None
            
        except Exception as e:
            logger.error(f"API check failed for {username}: {str(e)}")
            return None

    def signup_check(self, username):
        """Check username availability through signup API (most reliable)"""
        try:
            csr = token_hex(8) * 2
            uid = uuid4().hex.upper()
            miid = token_hex(13).upper()

            cookies = {
                'csrftoken': csr,
                'mid': miid,
                'ig_did': uid,
                'ig_nrcb': '1',
            }

            headers = {
                'authority': 'www.instagram.com',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://www.instagram.com',
                'referer': 'https://www.instagram.com/accounts/emailsignup/',
                'user-agent': generate_user_agent(),
                'x-asbd-id': '129477',
                'x-csrftoken': csr,
                'x-ig-app-id': '936619743392459',
                'x-ig-www-claim': '0',
            }

            data = {
                'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:randompassword',
                'email': 'temp@example.com',
                'first_name': 'Temp User',
                'username': username,
                'client_id': miid,
                'seamless_login_enabled': '1',
                'opt_into_one_tap': 'false',
            }

            response = requests.post(
                'https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/',
                cookies=cookies,
                headers=headers,
                data=data,
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                response_data = response.json()
                if 'dryrun_passed' in response_data and response_data['dryrun_passed']:
                    return True  # Available
                elif 'errors' in response_data and 'username_is_taken' in response_data['errors']:
                    return False  # Taken
            return None
            
        except Exception as e:
            logger.error(f"Signup check failed for {username}: {str(e)}")
            return None

def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message with channel join button"""
    keyboard = [[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "🌟 Welcome to the Instagram Username Generator Bot! 🌟\n\n"
        "🔹 Use /gen to generate available Instagram usernames\n"
        "🔹 Use /gen5 to generate 5 usernames at once\n"
        "🔹 Use /gen10 to generate 10 usernames at once\n"
        "🔹 Please join our channel for updates:",
        reply_markup=reply_markup
    )

def generate_usernames(update: Update, context: CallbackContext, count=1):
    """Generate and check Instagram usernames"""
    checker = InstagramChecker()
    patterns = [
        "#_#_#", "_#_#_", "##.##", "#.###", "##_##", "###__", "__###", 
        "**.**", "@@_§§", "§§.@@", "§§_@@", "@@.§§", "_###_", '**_""', 
        ".####", "#.#.#", "#_#.#", "#.#_#", "#.#_#", "##_##", "#_###", 
        "###_#", "#.##_", "##.##", "#.##.#", "#_##.#"
    ]
    
    try:
        # Send initial message with progress bar
        message = update.message.reply_text("🔍 Generating usernames...\n[░░░░░░░░░░] 0%")
        
        available_usernames = []
        total_checked = 0
        previous_count = 0
        
        while len(available_usernames) < count:
            # Update progress every 5 checks or when we find an available username
            if total_checked % 5 == 0 or (available_usernames and len(available_usernames) > previous_count):
                previous_count = len(available_usernames)
                progress = min(100, int((total_checked / (count * 3)) * 100))  # Estimate progress
                bars = int(progress / 10)
                progress_bar = f"[{'█' * bars}{'░' * (10 - bars)}] {progress}%"
                
                status_text = (
                    f"🔍 Generating usernames...\n"
                    f"{progress_bar}\n"
                    f"✅ Found: {len(available_usernames)}/{count}\n"
                    f"🔎 Checked: {total_checked}"
                )
                
                try:
                    context.bot.edit_message_text(
                        chat_id=message.chat_id,
                        message_id=message.message_id,
                        text=status_text
                    )
                except:
                    pass  # Skip edit if it fails
            
            pattern = random.choice(patterns)
            username = checker.generate_username(pattern)
            is_available = checker.check_instagram(username)
            total_checked += 1
            
            if is_available is True:
                available_usernames.append(username)
                checker.available_count += 1
            elif is_available is False:
                checker.unavailable_count += 1
            
            # Don't check too many if we're not finding available ones
            if total_checked > count * 10 and len(available_usernames) == 0:
                break
        
        # Final results
        if available_usernames:
            result_message = "🎉 Available Usernames:\n\n" + "\n".join([f"✅ @{username}" for username in available_usernames[:count]])
            result_message += f"\n\nStats: ✅ {len(available_usernames)} found | ❌ {checker.unavailable_count} taken | 🔎 {total_checked} checked"
        else:
            result_message = "😢 No available usernames found after checking many combinations. Try again!"
        
        # Edit the final message
        try:
            context.bot.edit_message_text(
                chat_id=message.chat_id,
                message_id=message.message_id,
                text=result_message[:4096]  # Telegram message limit
            )
        except:
            update.message.reply_text(result_message[:4096])
        
    except Exception as e:
        logger.error(f"Error in generate_usernames: {str(e)}")
        update.message.reply_text("❌ An error occurred. Please try again later.")
        # Notify admin
        if ADMIN_ID:
            context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🚨 Error in username generation:\n{str(e)}"
            )

def gen(update: Update, context: CallbackContext):
    """Generate single username"""
    generate_usernames(update, context, count=1)

def gen5(update: Update, context: CallbackQueryHandler):
    """Generate 5 usernames"""
    generate_usernames(update, context, count=5)

def gen10(update: Update, context: CallbackQueryHandler):
    """Generate 10 usernames"""
    generate_usernames(update, context, count=10)

def error_handler(update: Update, context: CallbackContext):
    """Log errors and notify admin"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if ADMIN_ID:
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ Bot Error:\n{context.error}\n\nUpdate: {update}"
        )

def main():
    """Start the bot"""
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("gen", gen))
    dp.add_handler(CommandHandler("gen5", gen5))
    dp.add_handler(CommandHandler("gen10", gen10))
    
    # Error handler
    dp.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
