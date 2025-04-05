import requests
from urllib.parse import quote
import re
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters
)

class XHamsterDownloaderBot:
    def __init__(self):
        self.api_endpoints = [
            "https://vkrdownloader.xyz/server/",
            "https://xhamsterdownloader.com/api/",
            "https://onlinevideoconverter.pro/api/"
        ]
        self.api_key = "free_api_key"  # Some services might require this
    
    def try_all_apis(self, xhamster_url: str) -> dict:
        """Try multiple APIs to get download links"""
        for endpoint in self.api_endpoints:
            try:
                encoded_url = quote(xhamster_url, safe='')
                api_url = f"{endpoint}?api_key={self.api_key}&url={encoded_url}"
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    result = self._parse_response(response.text)
                    if result:
                        return result
            except:
                continue
        return {}
    
    def _parse_response(self, html_content: str) -> dict:
        """Parse the HTML response to extract download links"""
        # Try multiple patterns to extract links
        patterns = [
            r'<a href="(https?://[^"]+)"[^>]*>(\d{3,4}p)</a>',
            r'download_url":"([^"]+)","quality":"(\d{3,4}p)',
            r'"(https?://[^"]+\.mp4)"[^>]+>(\d{3,4}p)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content)
            if matches:
                return {quality: link for link, quality in matches}
        return {}
    
    def get_download_options(self, xhamster_url: str) -> str:
        """Get download options for the given XHamster URL"""
        download_links = self.try_all_apis(xhamster_url)
        if not download_links:
            return "❌ Sorry, I couldn't find any working download options for this video.\n\nTry these alternatives:\n1. Use a VPN\n2. Try again later\n3. Try a different video"
        
        message = "📹 Available download qualities:\n"
        for quality in sorted(download_links.keys(), key=lambda x: int(x[:-1]), reverse=True):
            message += f"▫️ {quality}\n"
        message += "\n🔹 Reply with the quality you want (e.g., '720') to get the download link."
        return message
    
    def get_download_link(self, xhamster_url: str, quality: str) -> str:
        """Get the download link for a specific quality"""
        download_links = self.try_all_apis(xhamster_url)
        if not download_links:
            return "❌ Download options no longer available. Please send the link again."
        
        quality = quality.lower().replace('p', '') + 'p'
        for available_quality, link in download_links.items():
            if available_quality.lower() == quality.lower():
                return f"✅ Here's your {quality} download link:\n{link}\n\n⚠️ Link expires in 15 minutes"
        
        available = ", ".join(sorted(download_links.keys(), key=lambda x: int(x[:-1]), reverse=True))
        return f"❌ Quality {quality} not available. Options are: {available}"


async def start(update: Update, context: CallbackContext):
    """Send a welcome message when the command /start is issued"""
    await update.message.reply_text(
        "🤖 Welcome to XHamster Video Downloader Bot!\n\n"
        "🔹 Just send me an XHamster video link and I'll provide download options.\n"
        "🔹 Currently supported formats: 480p, 720p, 1080p\n\n"
        "⚠️ Note: Some videos might not be available due to regional restrictions"
    )

async def handle_xhamster_link(update: Update, context: CallbackContext):
    """Handle incoming XHamster links"""
    url = update.message.text.strip()
    if "xhamster.com" in url.lower():
        bot = XHamsterDownloaderBot()
        response = bot.get_download_options(url)
        await update.message.reply_text(response)
        context.user_data['last_xhamster_url'] = url
    else:
        await update.message.reply_text("❌ Please send a valid XHamster video URL")

async def handle_quality_choice(update: Update, context: CallbackContext):
    """Handle quality selection"""
    text = update.message.text.strip()
    if text.isdigit() and len(text) in (3, 4):
        bot = XHamsterDownloaderBot()
        original_url = context.user_data.get('last_xhamster_url')
        if original_url:
            response = bot.get_download_link(original_url, text)
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("⚠️ Please send an XHamster link first.")
    else:
        await update.message.reply_text("❌ Please enter a valid quality (e.g., 480, 720, 1080)")

def main():
    """Start the bot"""
    application = Application.builder().token("7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI").build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_xhamster_link))
    application.add_handler(MessageHandler(filters.Regex(r'^\d{3,4}$'), handle_quality_choice))
    
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
