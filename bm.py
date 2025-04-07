import os
import requests
import random
import time
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Your actual bot token
TOKEN = "7589335242:AAHHwteKQ7Keo4PRQVUv7nFlLV1tj1c3cYw"

# Proxy sources
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://api.openproxylist.xyz/http.txt"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def gen_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Gathering fresh proxies... Please wait!")

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
        await update.message.reply_text("❌ Failed to fetch proxies. Please try again later.")
        return

    selected_proxies = random.sample(list(proxies), min(100, len(proxies)))
    filename = f"proxies_{int(time.time())}.txt"
    with open(filename, 'w') as f:
        f.write("\n".join(selected_proxies))

    with open(filename, 'rb') as f:
        await update.message.reply_document(
            document=InputFile(f),
            caption=f"✅ Here are {len(selected_proxies)} fresh proxies!\n\n"
                    f"📝 Format: IP:PORT\n"
                    f"⏳ Generated at: {time.ctime()}"
        )
    os.remove(filename)

async def check_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("❌ Please reply to a .txt file with the /checkproxy command")
        return

    file = update.message.reply_to_message.document
    if not file.file_name.endswith('.txt'):
        await update.message.reply_text("❌ Please send a .txt file")
        return

    await update.message.reply_text("📥 Downloading your file...")
    file_obj = await context.bot.get_file(file.file_id)
    downloaded_file = await file_obj.download_to_drive()

    with open(downloaded_file, 'r') as f:
        proxies = [line.strip() for line in f.readlines() if line.strip()]

    if not proxies:
        await update.message.reply_text("❌ No proxies found in the file")
        os.remove(downloaded_file)
        return

    await update.message.reply_text(f"🔍 Found {len(proxies)} proxies. Checking validity... This may take a while.")

    working_proxies = []
    test_url = "http://www.google.com"

    for proxy in proxies:
        try:
            response = requests.get(
                test_url,
                proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                timeout=5
            )
            if response.status_code == 200:
                working_proxies.append(proxy)
        except:
            continue

    result_filename = f"checked_proxies_{int(time.time())}.txt"
    with open(result_filename, 'w') as f:
        f.write("\n".join(working_proxies))

    with open(result_filename, 'rb') as f:
        await update.message.reply_document(
            document=InputFile(f),
            caption=f"🔎 Proxy Check Results:\n\n"
                    f"✅ Working: {len(working_proxies)}\n"
                    f"❌ Failed: {len(proxies) - len(working_proxies)}\n"
                    f"⚡ Success Rate: {len(working_proxies)/len(proxies)*100:.1f}%"
        )

    os.remove(downloaded_file)
    os.remove(result_filename)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genproxy", gen_proxy))
    app.add_handler(CommandHandler("checkproxy", check_proxy))

    print("Bot is running...")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
