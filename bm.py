import random
import logging
import requests
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
        """Check if username is available on Instagram"""
        try:
            headers = {
                'User-Agent': generate_user_agent(),
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            # First check - simple profile lookup
            response = requests.get(
                f'https://www.instagram.com/{username}/',
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 404:
                # Profile doesn't exist - likely available
                return True
            elif response.status_code == 200:
                # Profile exists
                return False
                
            # If unclear, try API check
            return self.api_check(username)
            
        except Exception as e:
            logger.error(f"Error checking username {username}: {str(e)}")
            return None

    def api_check(self, username):
        """More advanced API check"""
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
            
            return response.status_code == 404
            
        except Exception as e:
            logger.error(f"API check failed for {username}: {str(e)}")
            return None

def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message with channel join button"""
    keyboard = [[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "🌟 Welcome to the Instagram Username Generator Bot! 🌟\n\n"
        "🔹 Use /gen to generate available Instagram usernames\n"
        "🔹 Use /gen5 to generate 5 usernames at once\n"
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
        update.message.reply_text("🔍 Generating usernames... Please wait")
        
        results = []
        for _ in range(count):
            pattern = random.choice(patterns)
            username = checker.generate_username(pattern)
            is_available = checker.check_instagram(username)
            
            if is_available is None:
                results.append(f"⚠️ @{username} - Check failed")
            elif is_available:
                results.append(f"✅ @{username} - Available!")
                checker.available_count += 1
            else:
                results.append(f"❌ @{username} - Taken")
                checker.unavailable_count += 1
        
        # Send results
        message = "📋 Username Generation Results:\n\n" + "\n".join(results)
        message += f"\n\nStats: ✅ {checker.available_count} available | ❌ {checker.unavailable_count} taken"
        update.message.reply_text(message[:4096])  # Telegram message limit
        
    except Exception as e:
        logger.error(f"Error in generate_usernames: {str(e)}")
        update.message.reply_text("❌ An error occurred. Please try again later.")
        # Notify admin
        context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🚨 Error in username generation:\n{str(e)}"
        )

def gen(update: Update, context: CallbackContext):
    """Generate single username"""
    generate_usernames(update, context, count=1)

def gen5(update: Update, context: CallbackContext):
    """Generate 5 usernames"""
    generate_usernames(update, context, count=5)

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
    updater = Updater(TOKEN)  # Removed use_context parameter
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("gen", gen))
    dp.add_handler(CommandHandler("gen5", gen5))
    
    # Error handler
    dp.add_error_handler(error_handler)

    # Start bot
    updater.start_polling()
    logger.info("Bot started and polling...")
    updater.idle()

if __name__ == '__main__':
    main()
