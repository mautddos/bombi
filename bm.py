import os
import random
import threading
import time
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram import InputFile

# Bot Token from BotFather
TOKEN = "7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI"

# Configuration constants
MAX_PROXIES = 1000
PROXY_TYPES = ['http', 'socks4', 'socks5']
PROXY_CHECK_TIMEOUT = 5  # seconds
MAX_PROXY_CHECK_THREADS = 20  # Limit concurrent checks

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    welcome_message = """
🌟 *Welcome to Unlimited Proxy Bot* 🌟

I can generate unlimited proxies for you and check their validity!

📌 *Available Commands:*
/gen_proxy - Generate proxies (send me a number)
/check - Check proxies from a .txt file
/help - Show help message

🚀 *Features:*
- Fast proxy generation
- Proxy validation
- Multiple proxy types
- Unlimited requests

Enjoy using me! 😊
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def gen_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask user how many proxies they want."""
    await update.message.reply_text(
        "🔢 *How many proxies do you want?* (Max 1000)", 
        parse_mode='Markdown'
    )

def generate_random_proxy() -> str:
    """Generate a random proxy."""
    proxy_type = random.choice(PROXY_TYPES)
    ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
    port = random.randint(1000, 9999)
    return f"{proxy_type}://{ip}:{port}"

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the number sent by user and generate proxies."""
    try:
        if (update.message.reply_to_message and 
            "How many proxies do you want?" in update.message.reply_to_message.text):
            num = int(update.message.text)
            if num <= 0:
                await update.message.reply_text("❌ Please enter a positive number!")
                return
            if num > MAX_PROXIES:
                await update.message.reply_text(
                    f"⚠️ Maximum limit is {MAX_PROXIES}. Generating {MAX_PROXIES} proxies."
                )
                num = MAX_PROXIES
            
            await update.message.reply_text(f"⚙️ Generating {num} proxies... Please wait!")
            
            # Generate proxies in a separate thread
            threading.Thread(
                target=generate_and_send_proxies, 
                args=(update, num),
                daemon=True
            ).start()
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number!")

async def generate_and_send_proxies(update: Update, num: int):
    """Generate proxies and send to user."""
    proxies = [generate_random_proxy() for _ in range(num)]
    filename = f"proxies_{int(time.time())}.txt"
    
    # Save to file
    with open(filename, "w") as f:
        f.write("\n".join(proxies))
    
    # Send as document
    with open(filename, "rb") as f:
        await update.message.reply_document(
            document=InputFile(f),
            caption=(
                f"✅ Successfully generated {num} proxies!\n\n"
                f"📝 *Proxy Types:* HTTP, SOCKS4, SOCKS5\n"
                f"📦 *Total Proxies:* {num}\n\n"
                "Enjoy! 😊"
            ),
            parse_mode='Markdown'
        )
    
    # Clean up
    os.remove(filename)

async def check_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask user to send proxy file for checking."""
    await update.message.reply_text(
        "📤 Please upload a .txt file containing proxies (one per line) to check their validity."
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the document sent by user for proxy checking."""
    if update.message.document:
        file = await update.message.document.get_file()
        filename = f"proxies_to_check_{int(time.time())}.txt"
        await file.download_to_drive(filename)
        
        await update.message.reply_text("🔍 Checking proxies... This may take a while!")
        
        # Check proxies in a separate thread
        threading.Thread(
            target=check_proxies_from_file, 
            args=(update, filename),
            daemon=True
        ).start()

def check_proxy_connection(proxy: str) -> bool:
    """Check if a proxy is valid."""
    try:
        # Implement actual proxy testing logic here
        return True  # Placeholder
    except Exception:
        return False

async def check_proxies_from_file(update: Update, filename: str):
    """Check proxies from file and send results."""
    try:
        with open(filename, 'r') as f:
            proxies = [line.strip() for line in f.readlines() if line.strip()]
        
        # [Rest of your proxy checking logic...]
        # Remember to use await when sending messages back to the user
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error checking proxies: {str(e)}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    help_text = """
🤖 *Proxy Bot Help* 🤖

*/gen_proxy* - Generate proxies. Bot will ask for quantity.
*/check* - Check proxies from a .txt file.
*/start* - Show welcome message.
*/help* - Show this help message.

📌 *Note:*
- Max 1000 proxies per generation
- Upload .txt file with one proxy per line for checking
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen_proxy", gen_proxy))
    application.add_handler(CommandHandler("check", check_proxy))
    application.add_handler(CommandHandler("help", help_command))

    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
    application.add_handler(MessageHandler(filters.Document.TXT, handle_document))

    # Run the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
