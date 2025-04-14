import os
import random
import requests
import time
from threading import Thread, Lock
from telegram import Bot, Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from concurrent.futures import ThreadPoolExecutor

# Bot Token from BotFather
TOKEN = "8102265512:AAGXrXgWir3LxkHlN8jruWTdXh7hOo8yasM"

# Initialize bot
bot = Bot(token=TOKEN)

# Proxy types for generation
PROXY_TYPES = ['http', 'socks4', 'socks5']

# For thread-safe progress tracking
progress_lock = Lock()
checking_status = {}

def generate_proxy(proxy_type):
    """Generate a random proxy"""
    ip = ".".join(str(random.randint(1, 255)) for _ in range(4))
    port = random.randint(1000, 9999)
    return f"{proxy_type}://{ip}:{port}"

def generate_proxies(count):
    """Generate multiple proxies"""
    proxies = []
    for _ in range(count):
        proxy_type = random.choice(PROXY_TYPES)
        proxies.append(generate_proxy(proxy_type))
    return proxies

def save_proxies_to_file(proxies, filename="proxies.txt"):
    """Save proxies to a text file"""
    with open(filename, 'w') as f:
        f.write("\n".join(proxies))
    return filename

def check_proxy(proxy, chat_id):
    """Check if a proxy is working and get its info"""
    try:
        start_time = time.time()
        response = requests.get(
            'http://ipinfo.io/json',
            proxies={'http': proxy, 'https': proxy},
            timeout=10
        )
        latency = int((time.time() - start_time) * 1000)  # in ms
        
        if response.status_code == 200:
            data = response.json()
            
            with progress_lock:
                checking_status[chat_id]['working'] += 1
                update_progress(chat_id)
            
            return {
                'proxy': proxy,
                'status': 'Working',
                'ip': data.get('ip', 'N/A'),
                'country': data.get('country', 'N/A'),
                'region': data.get('region', 'N/A'),
                'city': data.get('city', 'N/A'),
                'org': data.get('org', 'N/A'),
                'timezone': data.get('timezone', 'N/A'),
                'latency': f"{latency}ms"
            }
    except Exception as e:
        pass
    
    with progress_lock:
        checking_status[chat_id]['dead'] += 1
        update_progress(chat_id)
    
    return {
        'proxy': proxy,
        'status': 'Dead'
    }

def update_progress(chat_id):
    """Update the progress message"""
    status = checking_status[chat_id]
    total = status['total']
    checked = status['working'] + status['dead']
    progress = int(checked / total * 20)  # 20 characters for progress bar
    
    progress_bar = "[" + "■" * progress + " " * (20 - progress) + "]"
    text = (f"Checking proxies...\n"
            f"{progress_bar} {checked}/{total}\n"
            f"✅ Working: {status['working']}\n"
            f"❌ Dead: {status['dead']}\n"
            f"⏳ Remaining: {total - checked}")
    
    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=status['progress_msg_id'],
            text=text
        )
    except:
        pass  # Message wasn't modified

def check_proxies_from_file(filename, chat_id):
    """Check all proxies in a file"""
    with open(filename, 'r') as f:
        proxies = [line.strip() for line in f.readlines() if line.strip()]
    
    # Initialize progress tracking
    with progress_lock:
        checking_status[chat_id] = {
            'total': len(proxies),
            'working': 0,
            'dead': 0,
            'progress_msg_id': None
        }
    
    # Send initial progress message
    msg = bot.send_message(chat_id, "Starting proxy check...")
    with progress_lock:
        checking_status[chat_id]['progress_msg_id'] = msg.message_id
    
    working_proxies = []
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        # Map each proxy to the check_proxy function
        results = list(executor.map(lambda p: check_proxy(p, chat_id), proxies))
    
    working_proxies = [result for result in results if result['status'] == 'Working']
    
    # Create result file
    result_filename = f"checked_{filename}"
    with open(result_filename, 'w') as f:
        for proxy in results:
            if proxy['status'] == 'Working':
                f.write(f"Proxy: {proxy['proxy']}\n")
                f.write(f"Status: {proxy['status']}\n")
                f.write(f"IP: {proxy['ip']}\n")
                f.write(f"Country: {proxy['country']}\n")
                f.write(f"Region: {proxy['region']}\n")
                f.write(f"City: {proxy['city']}\n")
                f.write(f"Organization: {proxy['org']}\n")
                f.write(f"Timezone: {proxy['timezone']}\n")
                f.write(f"Latency: {proxy['latency']}\n")
                f.write("\n" + "="*50 + "\n\n")
            else:
                f.write(f"Proxy: {proxy['proxy']} - Status: {proxy['status']}\n\n")
    
    # Clean up progress tracking
    with progress_lock:
        del checking_status[chat_id]
    
    return result_filename, len(working_proxies), len(proxies)

def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        'Hi! I am a Proxy Bot.\n'
        'Commands:\n'
        '/gen [amount] - Generate proxies\n'
        '/check - Check proxies from file\n'
        'Send me a .txt file with proxies to check them'
    )

def gen_proxy(update: Update, context: CallbackContext):
    """Generate proxies"""
    try:
        # Get the amount from command
        amount = int(context.args[0]) if context.args else 100
        amount = min(amount, 10000)  # Limit to 10k to prevent abuse
        
        # Generate proxies
        proxies = generate_proxies(amount)
        
        # Save to file
        filename = save_proxies_to_file(proxies, f"proxies_{amount}.txt")
        
        # Send file
        with open(filename, 'rb') as f:
            update.message.reply_document(
                document=InputFile(f),
                caption=f"Here are your {amount} generated proxies"
            )
        
        # Clean up
        os.remove(filename)
        
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

def check_proxy_command(update: Update, context: CallbackContext):
    """Handle /check command"""
    update.message.reply_text(
        "Please send me a .txt file containing proxies to check. "
        "One proxy per line in format: protocol://ip:port"
    )

def handle_document(update: Update, context: CallbackContext):
    """Handle document upload for checking"""
    if not update.message.document.file_name.endswith('.txt'):
        update.message.reply_text("Please send a .txt file")
        return
    
    # Download the file
    file = context.bot.get_file(update.message.document.file_id)
    filename = update.message.document.file_name
    file.download(filename)
    
    # Check proxies in a separate thread to avoid blocking
    def check_and_send_results():
        chat_id = update.message.chat_id
        try:
            result_filename, working, total = check_proxies_from_file(filename, chat_id)
            
            # Send results
            with open(result_filename, 'rb') as f:
                update.message.reply_document(
                    document=InputFile(f),
                    caption=f"✅ Check complete!\nWorking: {working}\nDead: {total - working}\nSuccess rate: {working/total*100:.1f}%"
                )
            
            # Clean up
            os.remove(filename)
            os.remove(result_filename)
            
        except Exception as e:
            update.message.reply_text(f"Error: {str(e)}")
            if os.path.exists(filename):
                os.remove(filename)
    
    Thread(target=check_and_send_results).start()

def main():
    """Start the bot."""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("gen", gen_proxy))
    dp.add_handler(CommandHandler("check", check_proxy_command))
    
    # Document handler
    dp.add_handler(MessageHandler(Filters.document, handle_document))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
