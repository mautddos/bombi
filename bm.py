import os
import requests
import random
import time
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Replace with your actual bot token
TOKEN = "7589335242:AAHHwteKQ7Keo4PRQVUv7nFlLV1tj1c3cYw"

# Proxy sources (you can add more)
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://api.openproxylist.xyz/http.txt"
]

def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message when the command /start is issued."""
    welcome_text = """
    ✨ *Welcome to Proxy Master Bot* ✨

    I can help you with:
    - Generating fresh proxies 🆕
    - Checking proxy validity ✅

    🚀 *Commands:*
    /start - Show this welcome message
    /genproxy - Generate fresh proxies
    /checkproxy - Check proxies from a .txt file (reply to a file)

    📌 Just send me a command and I'll assist you!
    """
    update.message.reply_text(welcome_text, parse_mode='Markdown')

def gen_proxy(update: Update, context: CallbackContext) -> None:
    """Generate proxies and send as a text file."""
    update.message.reply_text("🔄 Gathering fresh proxies... Please wait!")
    
    proxies = set()
    
    for source in PROXY_SOURCES:
        try:
            response = requests.get(source, timeout=10)
            if response.status_code == 200:
                new_proxies = response.text.splitlines()
                proxies.update([p.strip() for p in new_proxies if p.strip()])
        except:
            continue
    
    if not proxies:
        update.message.reply_text("❌ Failed to fetch proxies. Please try again later.")
        return
    
    # Select random proxies (limit to 100 to avoid huge files)
    selected_proxies = random.sample(list(proxies), min(100, len(proxies)))
    
    # Create a temporary file
    filename = f"proxies_{int(time.time())}.txt"
    with open(filename, 'w') as f:
        f.write("\n".join(selected_proxies))
    
    # Send the file
    with open(filename, 'rb') as f:
        update.message.reply_document(
            document=InputFile(f),
            caption=f"✅ Here are {len(selected_proxies)} fresh proxies!\n\n"
                   f"📝 Format: IP:PORT\n"
                   f"⏳ Generated at: {time.ctime()}"
        )
    
    # Clean up
    os.remove(filename)

def check_proxy(update: Update, context: CallbackContext) -> None:
    """Check proxies from a text file."""
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        update.message.reply_text("❌ Please reply to a .txt file with the /checkproxy command")
        return
    
    file = update.message.reply_to_message.document
    if not file.file_name.endswith('.txt'):
        update.message.reply_text("❌ Please send a .txt file")
        return
    
    # Download the file
    update.message.reply_text("📥 Downloading your file...")
    file_obj = context.bot.get_file(file.file_id)
    downloaded_file = file_obj.download()
    
    # Read proxies
    with open(downloaded_file, 'r') as f:
        proxies = [line.strip() for line in f.readlines() if line.strip()]
    
    if not proxies:
        update.message.reply_text("❌ No proxies found in the file")
        os.remove(downloaded_file)
        return
    
    update.message.reply_text(f"🔍 Found {len(proxies)} proxies. Checking validity... This may take a while.")
    
    working_proxies = []
    test_url = "http://www.google.com"  # URL to test against
    
    for proxy in proxies:
        try:
            # Simple check - try to make a request with short timeout
            response = requests.get(
                test_url,
                proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                timeout=5
            )
            if response.status_code == 200:
                working_proxies.append(proxy)
        except:
            continue
    
    # Create result file
    result_filename = f"checked_proxies_{int(time.time())}.txt"
    with open(result_filename, 'w') as f:
        f.write("\n".join(working_proxies))
    
    # Send results
    with open(result_filename, 'rb') as f:
        update.message.reply_document(
            document=InputFile(f),
            caption=f"🔎 Proxy Check Results:\n\n"
                   f"✅ Working: {len(working_proxies)}\n"
                   f"❌ Failed: {len(proxies) - len(working_proxies)}\n"
                   f"⚡ Success Rate: {len(working_proxies)/len(proxies)*100:.1f}%"
        )
    
    # Clean up
    os.remove(downloaded_file)
    os.remove(result_filename)

def main() -> None:
    """Start the bot."""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("genproxy", gen_proxy))
    dispatcher.add_handler(CommandHandler("checkproxy", check_proxy))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
