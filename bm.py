import os
import re
import random
import time
import asyncio
import aiohttp
from datetime import datetime
from typing import List, Set
from telegram import Update, InputFile, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    Application
)

# Configuration
TOKEN = "8180063318:AAG2FtpVESnPYKuEszDIaewy-LXgVXXDS-o"
MAX_PROXIES_TO_RETURN = 500
PROXY_CHECK_TIMEOUT = 10
TEST_URL = "http://www.google.com"

# Enhanced proxy sources
PROXY_SOURCES = [
    {
        "url": "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        "type": "http",
        "format": "ip:port"
    },
    {
        "url": "https://www.proxy-list.download/api/v1/get?type=http",
        "type": "http",
        "format": "ip:port"
    },
    {
        "url": "https://api.openproxylist.xyz/http.txt",
        "type": "http",
        "format": "ip:port"
    },
    {
        "url": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
        "type": "http",
        "format": "ip:port"
    }
]

class ProxyBot:
    def __init__(self):
        self.session = None
        self.last_proxy_fetch = None
        self.cached_proxies = set()
    
    async def initialize(self):
        """Initialize the aiohttp session"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def validate_proxy(self, proxy: str) -> bool:
        """Check if a proxy is working"""
        try:
            async with self.session.get(
                TEST_URL,
                proxy=f"http://{proxy}",
                timeout=aiohttp.ClientTimeout(total=PROXY_CHECK_TIMEOUT)
            ) as response:
                # Check both status code and content length to ensure it's not just a connection
                return response.status == 200 and (await response.text())
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False
        except Exception:
            return False

    async def fetch_proxies_from_source(self, source: dict) -> Set[str]:
        """Fetch proxies from a single source"""
        try:
            async with self.session.get(source["url"], timeout=15) as response:
                if response.status == 200:
                    text = await response.text()
                    proxies = set()
                    for line in text.splitlines():
                        line = line.strip()
                        if line and re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+', line):
                            proxies.add(line)
                    return proxies
        except Exception as e:
            print(f"Error fetching from {source['url']}: {str(e)}")
        return set()

    async def get_fresh_proxies(self, max_proxies: int = MAX_PROXIES_TO_RETURN) -> List[str]:
        """Get fresh proxies from multiple sources"""
        if self.cached_proxies and self.last_proxy_fetch and (time.time() - self.last_proxy_fetch < 1800):
            return random.sample(list(self.cached_proxies), min(max_proxies, len(self.cached_proxies)))
        
        tasks = [self.fetch_proxies_from_source(source) for source in PROXY_SOURCES]
        results = await asyncio.gather(*tasks)
        
        new_proxies = set()
        for proxy_set in results:
            new_proxies.update(proxy_set)
        
        self.cached_proxies = new_proxies
        self.last_proxy_fetch = time.time()
        
        return random.sample(list(new_proxies), min(max_proxies, len(new_proxies)))

    async def check_proxies_from_file(self, file_path: str) -> List[str]:
        """Check proxies from a file and return working ones"""
        with open(file_path, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        
        if not proxies:
            return []
        
        # Check proxies in batches to avoid overwhelming the system
        batch_size = 20
        working_proxies = []
        
        for i in range(0, len(proxies), batch_size):
            batch = proxies[i:i + batch_size]
            tasks = [self.validate_proxy(proxy) for proxy in batch]
            results = await asyncio.gather(*tasks)
            working_proxies.extend([proxy for proxy, is_valid in zip(batch, results) if is_valid])
        
        return working_proxies

    def create_proxy_file(self, proxies: List[str], prefix: str = "proxies") -> str:
        """Create a temporary proxy file"""
        if not os.path.exists('temp'):
            os.makedirs('temp')
        filename = f"temp/{prefix}_{int(time.time())}.txt"
        with open(filename, 'w') as f:
            f.write("\n".join(proxies))
        return filename

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    welcome_text = """
🚀 *Proxy Master Bot* 🚀

Available commands:
/start - Show this message
/genproxy [amount] - Generate fresh proxies (default: 100, max: 500)
/checkproxy - Validate proxies (reply to a .txt file with proxies)
/stats - Show bot statistics

Examples:
/genproxy 50 - Get 50 fresh proxies
/genproxy - Get 100 proxies (default)
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def gen_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate proxies with amount handling"""
    bot = context.bot_data.get('proxy_bot')
    if not bot:
        await update.message.reply_text("❌ Bot initialization error")
        return
    
    # Default amount
    amount = 100
    
    # Check if user provided an amount
    if context.args:
        try:
            amount = int(context.args[0])
            if amount <= 0:
                await update.message.reply_text("❌ Please provide a positive number")
                return
            if amount > MAX_PROXIES_TO_RETURN:
                await update.message.reply_text(f"⚠️ Maximum is {MAX_PROXIES_TO_RETURN}. I'll return {MAX_PROXIES_TO_RETURN} proxies")
                amount = MAX_PROXIES_TO_RETURN
        except ValueError:
            await update.message.reply_text("❌ Please provide a valid number")
            return
    
    msg = await update.message.reply_text(f"🔄 Gathering {amount} proxies...")
    
    try:
        proxies = await bot.get_fresh_proxies(amount)
        if not proxies:
            await update.message.reply_text("❌ Failed to fetch proxies")
            return
        
        filename = bot.create_proxy_file(proxies)
        with open(filename, 'rb') as f:
            await update.message.reply_document(
                document=InputFile(f),
                caption=f"✅ {len(proxies)} fresh proxies\n\nFormat: ip:port"
            )
        os.remove(filename)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id
            )
        except Exception:
            pass

async def check_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check proxies from file with better feedback"""
    bot = context.bot_data.get('proxy_bot')
    if not bot:
        await update.message.reply_text("❌ Bot initialization error")
        return
    
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("❌ Please reply to a message containing a .txt file")
        return
    
    file = update.message.reply_to_message.document
    if not file.file_name.lower().endswith('.txt'):
        await update.message.reply_text("❌ Please send a .txt file")
        return
    
    msg = await update.message.reply_text("🔍 Checking proxies... This may take a while")
    
    try:
        # Download the file
        file_obj = await context.bot.get_file(file.file_id)
        downloaded_file = await file_obj.download_to_drive()
        
        # Count total proxies in file
        with open(downloaded_file, 'r') as f:
            total_proxies = sum(1 for line in f if line.strip())
        
        if total_proxies == 0:
            await update.message.reply_text("❌ The file is empty or contains no valid proxies")
            os.remove(downloaded_file)
            return
        
        # Update user on progress
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text=f"🔍 Checking {total_proxies} proxies... (0/{total_proxies})"
        )
        
        # Check proxies with progress updates
        working_proxies = await bot.check_proxies_from_file(downloaded_file)
        
        # Create result file
        if working_proxies:
            filename = bot.create_proxy_file(working_proxies, "working_proxies")
            with open(filename, 'rb') as f:
                await update.message.reply_document(
                    document=InputFile(f),
                    caption=f"✅ Working: {len(working_proxies)}\n❌ Failed: {total_proxies - len(working_proxies)}\n\nSuccess rate: {len(working_proxies)/total_proxies:.1%}"
                )
            os.remove(filename)
        else:
            await update.message.reply_text("❌ No working proxies found")
        
        os.remove(downloaded_file)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id
            )
        except Exception:
            pass

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show stats"""
    bot = context.bot_data.get('proxy_bot')
    if not bot:
        await update.message.reply_text("❌ Bot initialization error")
        return
    
    last_fetch = "Never" if not bot.last_proxy_fetch else datetime.fromtimestamp(bot.last_proxy_fetch).strftime('%Y-%m-%d %H:%M:%S')
    stats_text = f"""
📊 *Bot Statistics*:
🌐 Sources: {len(PROXY_SOURCES)}
📦 Cached proxies: {len(bot.cached_proxies)}
⏳ Last fetch: {last_fetch}
⚡ Max proxies per request: {MAX_PROXIES_TO_RETURN}
"""
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def setup_bot(application: Application):
    """Initialize bot"""
    proxy_bot = ProxyBot()
    await proxy_bot.initialize()
    application.bot_data['proxy_bot'] = proxy_bot
    
    await application.bot.set_my_commands([
        BotCommand("start", "Show help"),
        BotCommand("genproxy", "Generate proxies (default: 100)"),
        BotCommand("checkproxy", "Check proxies in file"),
        BotCommand("stats", "Show bot stats")
    ])

async def shutdown_bot(application: Application):
    """Cleanup bot"""
    if 'proxy_bot' in application.bot_data:
        await application.bot_data['proxy_bot'].close()
    # Clean temp files
    if os.path.exists('temp'):
        for file in os.listdir('temp'):
            os.remove(f"temp/{file}")
        os.rmdir('temp')

def run_bot():
    """Run the bot with proper event loop handling"""
    # Create the Application and pass it your bot's token.
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("genproxy", gen_proxy))
    application.add_handler(CommandHandler("checkproxy", check_proxy))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    
    # Setup initialization and shutdown
    application.post_init = setup_bot
    application.post_shutdown = shutdown_bot
    
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
