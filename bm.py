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
TOKEN = "7589335242:AAHHwteKQ7Keo4PRQVUv7nFlLV1tj1c3cYw"  # Replace with your actual token
MAX_PROXIES_TO_RETURN = 500
PROXY_CHECK_TIMEOUT = 10
TEST_URL = "http://www.google.com"

# Enhanced proxy sources with metadata
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
        if self.session:
            await self.session.close()

    async def validate_proxy(self, proxy: str) -> bool:
        """Check if a proxy is working"""
        try:
            async with self.session.get(
                TEST_URL,
                proxy=f"http://{proxy}",
                timeout=PROXY_CHECK_TIMEOUT
            ) as response:
                return response.status == 200
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
        # Use cache if recent (within 30 minutes)
        if self.cached_proxies and self.last_proxy_fetch and (time.time() - self.last_proxy_fetch < 1800):
            return random.sample(list(self.cached_proxies), min(max_proxies, len(self.cached_proxies)))
        
        # Fetch new proxies
        tasks = [self.fetch_proxies_from_source(source) for source in PROXY_SOURCES]
        results = await asyncio.gather(*tasks)
        
        # Combine and deduplicate
        new_proxies = set()
        for proxy_set in results:
            new_proxies.update(proxy_set)
        
        # Update cache
        self.cached_proxies = new_proxies
        self.last_proxy_fetch = time.time()
        
        return random.sample(list(new_proxies), min(max_proxies, len(new_proxies)))

    async def check_proxies_from_file(self, file_path: str) -> List[str]:
        """Check proxies from a file and return working ones"""
        with open(file_path, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        
        if not proxies:
            return []
        
        # Validate proxies in parallel
        tasks = [self.validate_proxy(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks)
        
        return [proxy for proxy, is_valid in zip(proxies, results) if is_valid]

    def create_proxy_file(self, proxies: List[str], prefix: str = "proxies") -> str:
        """Create a temporary proxy file"""
        filename = f"{prefix}_{int(time.time())}.txt"
        with open(filename, 'w') as f:
            f.write("\n".join(proxies))
        return filename

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with bot commands"""
    welcome_text = """
🚀 *Proxy Master Bot - Premium Proxy Service* 🚀

I specialize in high-quality proxy services with:
- Fresh proxy generation 🆕
- Proxy validation ✅
- Multiple sources 🌐
- Fast checking ⚡

📋 *Available Commands:*
/start - Show this message
/genproxy - Generate fresh proxies (HTTP)
/checkproxy - Check proxies from a .txt file (reply to file)
/stats - Show bot statistics

🔧 *Advanced Options:*
/genproxy <number> - Get specific number of proxies (max 500)
/genproxy <country> - Get proxies from specific country (US, UK, etc.)
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def gen_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send fresh proxies"""
    bot = context.bot_data.get('proxy_bot')
    if not bot:
        await update.message.reply_text("❌ Bot initialization error. Please try again.")
        return
    
    # Parse command arguments
    args = context.args
    max_proxies = MAX_PROXIES_TO_RETURN
    
    if args and args[0].isdigit():
        max_proxies = min(int(args[0]), MAX_PROXIES_TO_RETURN)
    
    processing_msg = await update.message.reply_text(
        f"🔄 Gathering {max_proxies} fresh proxies... This may take a moment."
    )
    
    try:
        proxies = await bot.get_fresh_proxies(max_proxies)
        
        if not proxies:
            await update.message.reply_text("❌ Failed to fetch proxies. Please try again later.")
            return
        
        filename = bot.create_proxy_file(proxies)
        
        with open(filename, 'rb') as f:
            await update.message.reply_document(
                document=InputFile(f),
                caption=(
                    f"✅ *Proxy List Generated*\n\n"
                    f"📊 Count: {len(proxies)}\n"
                    f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"🌐 Type: HTTP\n\n"
                    f"🔧 Use /checkproxy to validate these proxies"
                ),
                parse_mode='Markdown'
            )
        
        os.remove(filename)
    except Exception as e:
        await update.message.reply_text(f"❌ Error generating proxies: {str(e)}")
    finally:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id
            )
        except Exception:
            pass

async def check_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check proxies from a file"""
    bot = context.bot_data.get('proxy_bot')
    if not bot:
        await update.message.reply_text("❌ Bot initialization error. Please try again.")
        return
    
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("❌ Please reply to a .txt file with the /checkproxy command")
        return
    
    file = update.message.reply_to_message.document
    if not file.file_name.lower().endswith('.txt'):
        await update.message.reply_text("❌ Please send a .txt file")
        return
    
    processing_msg = await update.message.reply_text("📥 Downloading and checking your proxies...")
    
    try:
        file_obj = await context.bot.get_file(file.file_id)
        downloaded_file = await file_obj.download_to_drive()
        
        working_proxies = await bot.check_proxies_from_file(downloaded_file)
        total_proxies = sum(1 for _ in open(downloaded_file))
        
        if not working_proxies:
            await update.message.reply_text("❌ No working proxies found in the file")
            return
        
        result_file = bot.create_proxy_file(working_proxies, "working_proxies")
        
        with open(result_file, 'rb') as f:
            await update.message.reply_document(
                document=InputFile(f),
                caption=(
                    f"🔍 *Proxy Check Results*\n\n"
                    f"✅ Working: {len(working_proxies)}\n"
                    f"❌ Failed: {total_proxies - len(working_proxies)}\n"
                    f"⚡ Success Rate: {len(working_proxies)/total_proxies*100:.1f}%\n\n"
                    f"🕒 Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                parse_mode='Markdown'
            )
        
        os.remove(downloaded_file)
        os.remove(result_file)
    except Exception as e:
        await update.message.reply_text(f"❌ Error checking proxies: {str(e)}")
    finally:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=processing_msg.message_id
            )
        except Exception:
            pass

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics"""
    bot = context.bot_data.get('proxy_bot')
    if not bot:
        await update.message.reply_text("❌ Bot initialization error. Please try again.")
        return
    
    last_fetch = "Never" if not bot.last_proxy_fetch else datetime.fromtimestamp(bot.last_proxy_fetch).strftime('%Y-%m-%d %H:%M:%S')
    
    stats_text = (
        "📊 *Proxy Master Bot Statistics*\n\n"
        f"🌐 Proxy Sources: {len(PROXY_SOURCES)}\n"
        f"📦 Cached Proxies: {len(bot.cached_proxies)}\n"
        f"⏳ Last Fetch: {last_fetch}\n\n"
        "🔄 The bot automatically caches proxies for 30 minutes"
    )
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def post_init(application: Application):
    """Initialize bot after startup"""
    proxy_bot = ProxyBot()
    await proxy_bot.initialize()
    application.bot_data['proxy_bot'] = proxy_bot
    
    # Set bot commands
    commands = [
        BotCommand("start", "Show welcome message"),
        BotCommand("genproxy", "Generate fresh proxies"),
        BotCommand("checkproxy", "Check proxies from file"),
        BotCommand("stats", "Show bot statistics")
    ]
    await application.bot.set_my_commands(commands)

async def post_shutdown(application: Application):
    """Cleanup resources before shutdown"""
    if 'proxy_bot' in application.bot_data:
        await application.bot_data['proxy_bot'].close()

async def main():
    """Main application entry point"""
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).post_shutdown(post_shutdown).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("genproxy", gen_proxy))
    application.add_handler(CommandHandler("checkproxy", check_proxy))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    
    print("Bot is starting...")
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
