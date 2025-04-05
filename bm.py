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
        self.api_base = "https://vkrdownloader.xyz/server/"
        self.api_key = "vkrdownloader"
    
    def process_link(self, xhamster_url: str) -> dict:
        """Process the XHamster URL through the vkrdownloader API"""
        try:
            encoded_url = quote(xhamster_url, safe='')
            api_url = f"{self.api_base}?api_key={self.api_key}&vkr={encoded_url}"
            response = requests.get(api_url)
            
            if response.status_code == 200:
                return self._parse_response(response.text)
            return {}
        except Exception as e:
            print(f"Error processing link: {e}")
            return {}
    
    def _parse_response(self, html_content: str) -> dict:
        """Parse the HTML response to extract download links"""
        pattern = r'<a href="(https?://[^"]+)"[^>]*>(\d{3,4}p)</a>'
        matches = re.findall(pattern, html_content)
        return {quality: link for link, quality in matches}
    
    def get_download_options(self, xhamster_url: str) -> str:
        """Get download options for the given XHamster URL"""
        download_links = self.process_link(xhamster_url)
        if not download_links:
            return "❌ Sorry, I couldn't process that XHamster link."
        
        message = "📹 Available download qualities:\n"
        for quality in sorted(download_links.keys(), key=lambda x: int(x[:-1]), reverse=True):
            message += f"▫️ {quality}\n"
        message += "\n🔹 Reply with the quality you want (e.g., '720') to get the download link."
        return message
    
    def get_download_link(self, xhamster_url: str, quality: str) -> str:
        """Get the download link for a specific quality"""
        download_links = self.process_link(xhamster_url)
        if not download_links:
            return "❌ Sorry, I couldn't process that XHamster link."
        
        quality = quality.lower().replace('p', '') + 'p'
        for available_quality, link in download_links.items():
            if available_quality.lower() == quality.lower():
                return f"✅ Here's your {quality} download link:\n{link}"
        
        available = ", ".join(sorted(download_links.keys(), key=lambda x: int(x[:-1]), reverse=True))
        return f"❌ Quality {quality} not available. Options are: {available}"


async def start(update: Update, context: CallbackContext):
    """Send a welcome message when the command /start is issued"""
    await update.message.reply_text(
        "🤖 Welcome to XHamster Video Downloader Bot!\n\n"
        "🔹 Just send me an XHamster video link and I'll provide download options."
    )

async def handle_xhamster_link(update: Update, context: CallbackContext):
    """Handle incoming XHamster links"""
    url = update.message.text.strip()
    if "xhamster.com" in url.lower():
        bot = XHamsterDownloaderBot()
        response = bot.get_download_options(url)
        await update.message.reply_text(response)
        context.user_data['last_xhamster_url'] = url

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

def main():
    """Start the bot"""
    # Create the Application and pass it your bot's token
    application = Application.builder().token("7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI").build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_xhamster_link))
    application.add_handler(MessageHandler(filters.Regex(r'^\d{3,4}$'), handle_quality_choice))
    
    # Run the bot until you press Ctrl-C
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
