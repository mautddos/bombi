import os
import re
import random
import time
import asyncio
import aiohttp
import json
from datetime import datetime
from typing import List, Set, Dict, Optional
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
MAX_PROXIES_PER_FILE = 500  # To avoid too large files
PROXY_CHECK_TIMEOUT = 10
TEST_URL = "http://www.google.com"
IPINFO_API = "https://ipinfo.io/{}/json"  # Free tier has 50k/month
IPAPI_API = "http://ip-api.com/json/{}"  # Free tier has 45 requests/minute

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
    },
    {
        "url": "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt",
        "type": "http",
        "format": "ip:port"
    }
]

class ProxyBot:
    def __init__(self):
        self.session = None
        self.last_proxy_fetch = None
        self.cached_proxies = set()
        self.geo_cache = {}  # Cache for IP geolocation
    
    async def initialize(self):
        """Initialize the aiohttp session"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_ip_info(self, ip: str) -> Optional[Dict]:
        """Get geolocation info for an IP"""
        if ip in self.geo_cache:
            return self.geo_cache[ip]
        
        try:
            async with self.session.get(IPAPI_API.format(ip), timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'success':
                        self.geo_cache[ip] = data
                        return data
        except Exception:
            pass
        
        try:
            async with self.session.get(IPINFO_API.format(ip), timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    self.geo_cache[ip] = data
                    return data
        except Exception:
            pass
        
        return None

    async def validate_proxy(self, proxy: str) -> Dict:
        """Check if a proxy is working and return detailed info"""
        ip = proxy.split(':')[0]
        result = {
            'proxy': proxy,
            'working': False,
            'country': 'Unknown',
            'region': 'Unknown',
            'city': 'Unknown',
            'org': 'Unknown',
            'latency': None
        }
        
        try:
            start_time = time.time()
            async with self.session.get(
                TEST_URL,
                proxy=f"http://{proxy}",
                timeout=aiohttp.ClientTimeout(total=PROXY_CHECK_TIMEOUT)
            ) as response:
                if response.status == 200:
                    result['working'] = True
                    result['latency'] = round((time.time() - start_time) * 1000, 2)  # ms
                    
                    # Get geolocation info
                    geo_info = await self.get_ip_info(ip)
                    if geo_info:
                        result.update({
                            'country': geo_info.get('country', 'Unknown'),
                            'region': geo_info.get('region', 'Unknown'),
                            'city': geo_info.get('city', 'Unknown'),
                            'org': geo_info.get('org', geo_info.get('isp', 'Unknown'))
                        })
        except Exception as e:
            pass
        
        return result

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

    async def get_fresh_proxies(self, max_proxies: int = None) -> List[str]:
        """Get fresh proxies from multiple sources"""
        if self.cached_proxies and self.last_proxy_fetch and (time.time() - self.last_proxy_fetch < 1800):
            proxies = list(self.cached_proxies)
            if max_proxies:
                return random.sample(proxies, min(max_proxies, len(proxies)))
            return proxies
        
        tasks = [self.fetch_proxies_from_source(source) for source in PROXY_SOURCES]
        results = await asyncio.gather(*tasks)
        
        new_proxies = set()
        for proxy_set in results:
            new_proxies.update(proxy_set)
        
        self.cached_proxies = new_proxies
        self.last_proxy_fetch = time.time()
        
        proxies = list(new_proxies)
        if max_proxies:
            return random.sample(proxies, min(max_proxies, len(proxies)))
        return proxies

    async def check_proxies_from_file(self, file_path: str) -> List[Dict]:
        """Check proxies from a file and return detailed info"""
        with open(file_path, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        
        if not proxies:
            return []
        
        # Check proxies in batches
        batch_size = 10  # Smaller batch size for geo lookups
        checked_proxies = []
        
        for i in range(0, len(proxies), batch_size):
            batch = proxies[i:i + batch_size]
            tasks = [self.validate_proxy(proxy) for proxy in batch]
            results = await asyncio.gather(*tasks)
            checked_proxies.extend(results)
            await asyncio.sleep(1)  # Rate limiting for geo API
        
        return checked_proxies

    def create_proxy_file(self, proxies: List[str], prefix: str = "proxies") -> str:
        """Create a temporary proxy file"""
        if not os.path.exists('temp'):
            os.makedirs('temp')
        filename = f"temp/{prefix}_{int(time.time())}.txt"
        with open(filename, 'w') as f:
            f.write("\n".join(proxies))
        return filename

    def create_detailed_report(self, proxies: List[Dict], prefix: str = "report") -> str:
        """Create a detailed CSV report"""
        if not os.path.exists('temp'):
            os.makedirs('temp')
        filename = f"temp/{prefix}_{int(time.time())}.csv"
        
        with open(filename, 'w') as f:
            f.write("Status,Proxy,Country,Region,City,Organization,Latency(ms)\n")
            for proxy in proxies:
                status = "✅" if proxy['working'] else "❌"
                f.write(f"{status},{proxy['proxy']},{proxy['country']},{proxy['region']},"
                        f"{proxy['city']},{proxy['org']},{proxy['latency'] or ''}\n")
        
        return filename

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    welcome_text = """
🚀 *Advanced Proxy Bot* 🚀

Available commands:
/start - Show this message
/genproxy [amount] - Generate proxies (default: all, max per file: 500)
/massproxy [total] [per_file] - Generate large amounts with multiple files
/checkproxy - Validate proxies (reply to .txt file)
/stats - Show bot statistics

Examples:
/genproxy - Get all available proxies
/genproxy 100 - Get 100 random proxies
/massproxy 1000 200 - Get 1000 proxies in 5 files of 200 each
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def gen_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate proxies with optional amount"""
    bot = context.bot_data.get('proxy_bot')
    if not bot:
        await update.message.reply_text("❌ Bot initialization error")
        return
    
    amount = None
    if context.args and context.args[0].isdigit():
        amount = min(int(context.args[0]), MAX_PROXIES_PER_FILE)
    
    msg = await update.message.reply_text(f"🔄 Gathering {'all' if not amount else amount} proxies...")
    
    try:
        proxies = await bot.get_fresh_proxies(amount)
        if not proxies:
            await update.message.reply_text("❌ Failed to fetch proxies")
            return
        
        filename = bot.create_proxy_file(proxies)
        with open(filename, 'rb') as f:
            await update.message.reply_document(
                document=InputFile(f),
                caption=f"✅ {len(proxies)} proxies\n\nFormat: ip:port"
            )
        os.remove(filename)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
        except Exception:
            pass

async def mass_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate large amounts of proxies in multiple files"""
    bot = context.bot_data.get('proxy_bot')
    if not bot:
        await update.message.reply_text("❌ Bot initialization error")
        return
    
    if not context.args or len(context.args) < 2 or not all(arg.isdigit() for arg in context.args[:2]):
        await update.message.reply_text("❌ Usage: /massproxy [total_amount] [proxies_per_file]")
        return
    
    total = int(context.args[0])
    per_file = min(int(context.args[1]), MAX_PROXIES_PER_FILE)
    files_needed = (total + per_file - 1) // per_file
    
    if total > 10000:
        await update.message.reply_text("⚠️ Very large amounts may take long time to gather")
    
    msg = await update.message.reply_text(f"🔄 Gathering {total} proxies in {files_needed} files...")
    
    try:
        all_proxies = await bot.get_fresh_proxies()  # Get all available
        if not all_proxies:
            await update.message.reply_text("❌ Failed to fetch proxies")
            return
        
        # Shuffle and take requested amount
        random.shuffle(all_proxies)
        proxies = all_proxies[:min(total, len(all_proxies))]
        
        # Split into chunks
        for i in range(0, len(proxies), per_file):
            chunk = proxies[i:i + per_file]
            filename = bot.create_proxy_file(chunk, f"proxies_{i//per_file+1}")
            with open(filename, 'rb') as f:
                await update.message.reply_document(
                    document=InputFile(f),
                    caption=f"📁 File {i//per_file + 1}/{files_needed} - {len(chunk)} proxies"
                )
            os.remove(filename)
        
        await update.message.reply_text(f"✅ Sent {len(proxies)} proxies in {files_needed} files")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
        except Exception:
            pass

async def check_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check proxies with detailed report"""
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
    
    msg = await update.message.reply_text("🔍 Checking proxies... This may take several minutes")
    
    try:
        file_obj = await context.bot.get_file(file.file_id)
        downloaded_file = await file_obj.download_to_drive()
        
        # Count total proxies
        with open(downloaded_file, 'r') as f:
            total = sum(1 for line in f if line.strip())
        
        if total == 0:
            await update.message.reply_text("❌ The file is empty or contains no valid proxies")
            os.remove(downloaded_file)
            return
        
        # Check proxies
        checked_proxies = await bot.check_proxies_from_file(downloaded_file)
        working_proxies = [p for p in checked_proxies if p['working']]
        
        # Create detailed report
        report_file = bot.create_detailed_report(checked_proxies)
        
        # Send results
        result_text = (
            f"📊 Proxy Check Results:\n"
            f"✅ Working: {len(working_proxies)}\n"
            f"❌ Failed: {len(checked_proxies) - len(working_proxies)}\n"
            f"📝 Success rate: {len(working_proxies)/len(checked_proxies):.1%}"
        )
        
        with open(report_file, 'rb') as f:
            await update.message.reply_document(
                document=InputFile(f),
                caption=result_text
            )
        
        # Send working proxies separately
        if working_proxies:
            working_file = bot.create_proxy_file([p['proxy'] for p in working_proxies], "working_proxies")
            with open(working_file, 'rb') as f:
                await update.message.reply_document(
                    document=InputFile(f),
                    caption="✅ Working proxies"
                )
            os.remove(working_file)
        
        os.remove(downloaded_file)
        os.remove(report_file)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
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
📁 Max per file: {MAX_PROXIES_PER_FILE}
"""
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def setup_bot(application: Application):
    """Initialize bot"""
    proxy_bot = ProxyBot()
    await proxy_bot.initialize()
    application.bot_data['proxy_bot'] = proxy_bot
    
    await application.bot.set_my_commands([
        BotCommand("start", "Show help"),
        BotCommand("genproxy", "Generate proxies"),
        BotCommand("massproxy", "Generate large amounts"),
        BotCommand("checkproxy", "Check proxies"),
        BotCommand("stats", "Show stats")
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
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("genproxy", gen_proxy))
    application.add_handler(CommandHandler("massproxy", mass_proxy))
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
