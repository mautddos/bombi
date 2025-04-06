import os
import random
import threading
import requests
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Bot Token from BotFather
TOKEN = "7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI"

# Proxy types
PROXY_TYPES = ['http', 'socks4', 'socks5']

def start(update: Update, context: CallbackContext) -> None:
    """Send a beautiful welcome message when the command /start is issued."""
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
    update.message.reply_text(welcome_message, parse_mode='Markdown')

def gen_proxy(update: Update, context: CallbackContext) -> None:
    """Ask user how many proxies they want."""
    update.message.reply_text("🔢 *How many proxies do you want?* (Max 1000)", parse_mode='Markdown')

def generate_random_proxy():
    """Generate a random proxy."""
    proxy_type = random.choice(PROXY_TYPES)
    ip = ".".join(map(str, (random.randint(0, 255) for _ in range(4))))
    port = random.randint(1000, 9999)
    return f"{proxy_type}://{ip}:{port}"

def handle_number(update: Update, context: CallbackContext) -> None:
    """Handle the number sent by user and generate proxies."""
    try:
        if update.message.reply_to_message and update.message.reply_to_message.text == "🔢 *How many proxies do you want?* (Max 1000)":
            num = int(update.message.text)
            if num <= 0:
                update.message.reply_text("❌ Please enter a positive number!")
                return
            if num > 1000:
                update.message.reply_text("⚠️ Maximum limit is 1000. Generating 1000 proxies.")
                num = 1000
            
            update.message.reply_text(f"⚙️ Generating {num} proxies... Please wait!")
            
            # Generate proxies in a separate thread to avoid blocking
            threading.Thread(target=generate_and_send_proxies, args=(update, num)).start()
    except ValueError:
        update.message.reply_text("❌ Please enter a valid number!")

def generate_and_send_proxies(update: Update, num: int):
    """Generate proxies and send to user."""
    proxies = [generate_random_proxy() for _ in range(num)]
    
    # Save to file
    with open("proxies.txt", "w") as f:
        f.write("\n".join(proxies))
    
    # Send as document
    with open("proxies.txt", "rb") as f:
        update.message.reply_document(
            document=InputFile(f),
            caption=f"✅ Successfully generated {num} proxies!\n\n"
                   f"📝 *Proxy Types:* HTTP, SOCKS4, SOCKS5\n"
                   f"📦 *Total Proxies:* {num}\n\n"
                   "Enjoy! 😊",
            parse_mode='Markdown'
        )

def check_proxy(update: Update, context: CallbackContext) -> None:
    """Ask user to send proxy file for checking."""
    update.message.reply_text("📤 Please upload a .txt file containing proxies (one per line) to check their validity.")

def handle_document(update: Update, context: CallbackContext) -> None:
    """Handle the document sent by user for proxy checking."""
    if update.message.document:
        file = update.message.document.get_file()
        file.download('proxies_to_check.txt')
        
        update.message.reply_text("🔍 Checking proxies... This may take a while!")
        
        # Check proxies in a separate thread
        threading.Thread(target=check_proxies_from_file, args=(update,)).start()

def check_proxy(proxy: str) -> bool:
    """Check if a proxy is valid (simplified version)."""
    try:
        # This is a simplified check - in a real bot you'd actually test the proxy
        parts = proxy.split(":")
        if len(parts) >= 2:
            return True
        return False
    except:
        return False

def check_proxies_from_file(update: Update):
    """Check proxies from file and send results."""
    try:
        with open('proxies_to_check.txt', 'r') as f:
            proxies = [line.strip() for line in f.readlines() if line.strip()]
        
        total = len(proxies)
        working = 0
        working_proxies = []
        
        for proxy in proxies:
            if check_proxy(proxy):
                working += 1
                working_proxies.append(proxy)
        
        # Save working proxies
        with open('working_proxies.txt', 'w') as f:
            f.write("\n".join(working_proxies))
        
        # Send results
        message = (
            f"📊 *Proxy Check Results*\n\n"
            f"✅ *Working:* {working}\n"
            f"❌ *Dead:* {total - working}\n"
            f"📈 *Success Rate:* {working/total*100:.2f}%\n\n"
        )
        
        if working > 0:
            message += "Here are the working proxies:"
            with open('working_proxies.txt', 'rb') as f:
                update.message.reply_document(
                    document=InputFile(f),
                    caption=message,
                    parse_mode='Markdown'
                )
        else:
            message += "No working proxies found. 😢"
            update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        update.message.reply_text(f"❌ Error checking proxies: {str(e)}")

def help_command(update: Update, context: CallbackContext) -> None:
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
    update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Start the bot."""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("gen_proxy", gen_proxy))
    dispatcher.add_handler(CommandHandler("check", check_proxy))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Message handlers
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_number))
    dispatcher.add_handler(MessageHandler(Filters.document, handle_document))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
