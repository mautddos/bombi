import requests
from urllib.parse import quote
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import logging
from typing import Dict, Optional, Tuple

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

class XHamsterDownloader:
    def __init__(self):
        self.api_base = "https://vkrdownloader.xyz/server/"
        self.api_key = "vkrdownloader"
        self.user_sessions = {}  # Stores user_id: {'url': xhamster_url, 'links': download_links}

    def process_link(self, xhamster_url: str) -> Optional[Dict[str, str]]:
        """Process the XHamster URL through the vkrdownloader API"""
        try:
            # Validate URL format
            if not self._validate_xhamster_url(xhamster_url):
                return None

            # Encode the URL for the API request
            encoded_url = quote(xhamster_url, safe='')
            
            # Make the API request
            api_url = f"{self.api_base}?api_key={self.api_key}&vkr={encoded_url}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"API request failed with status code: {response.status_code}")
                return None

            return self._parse_response(response.text)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error processing link: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing link: {e}")
            return None

    def _validate_xhamster_url(self, url: str) -> bool:
        """Validate that the URL is a proper XHamster URL"""
        pattern = r'^https?://(www\.)?xhamster\.com/videos/[a-zA-Z0-9\-]+'
        return re.match(pattern, url) is not None

    def _parse_response(self, html_content: str) -> Dict[str, str]:
        """Parse the HTML response to extract download links"""
        # This regex looks for download links in the response HTML
        pattern = r'<a href="(https?://[^"]+)"[^>]*>(\d{3,4}p)</a>'
        matches = re.findall(pattern, html_content)
        
        download_links = {}
        for link, quality in matches:
            # Only include standard quality options
            if quality in ['480p', '720p', '1080p']:
                download_links[quality] = link
        
        return download_links

    def get_download_options(self, user_id: int, xhamster_url: str) -> Tuple[Optional[Dict[str, str]], str]:
        """Get download options for the given XHamster URL"""
        # First check if we already processed this URL recently
        if user_id in self.user_sessions and self.user_sessions[user_id]['url'] == xhamster_url:
            return self.user_sessions[user_id]['links'], "found_in_cache"
        
        download_links = self.process_link(xhamster_url)
        
        if not download_links:
            return None, "api_failure"
        
        # Store the links in user session
        self.user_sessions[user_id] = {
            'url': xhamster_url,
            'links': download_links
        }
        
        return download_links, "success"

# Initialize the downloader
downloader = XHamsterDownloader()

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_text(
        f"Hi {user.first_name}! Send me an XHamster video link and I'll provide download options."
    )

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        "Just send me a valid XHamster video URL (like https://xhamster.com/videos/...) "
        "and I'll give you download options!"
    )

def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle the user message containing XHamster URL."""
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    # Check if it's a response to quality selection (handled by callback)
    if message_text.isdigit() and len(message_text) in (3, 4):
        return
    
    # Process as XHamster URL
    download_links, status = downloader.get_download_options(user_id, message_text)
    
    if status == "api_failure":
        update.message.reply_text("Sorry, I couldn't process that link. Please check the URL and try again.")
        return
    elif not download_links:
        update.message.reply_text("This doesn't appear to be a valid XHamster video URL. Please send a valid URL.")
        return
    
    # Create inline keyboard with available quality options
    keyboard = []
    for quality in sorted(download_links.keys(), reverse=True):
        keyboard.append([InlineKeyboardButton(quality, callback_data=quality)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose a video quality:', reply_markup=reply_markup)

def button_callback(update: Update, context: CallbackContext) -> None:
    """Handle button callbacks for quality selection."""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get the selected quality
    selected_quality = query.data
    
    # Get the stored download links for this user
    if user_id not in downloader.user_sessions:
        query.answer("Session expired. Please send the URL again.")
        return
    
    download_links = downloader.user_sessions[user_id]['links']
    
    if selected_quality not in download_links:
        query.answer("Selected quality not available anymore.")
        return
    
    # Get the download link
    download_url = download_links[selected_quality]
    
    # Edit the original message to show the download link
    query.edit_message_text(
        text=f"Here's your {selected_quality} download link:\n\n{download_url}\n\n"
             "Note: The link may expire after some time. If it doesn't work, request a new one."
    )
    query.answer()

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors caused by updates."""
    logger.error('Update "%s" caused error "%s"', update, context.error)
    if update.effective_message:
        update.effective_message.reply_text('An error occurred. Please try again later.')

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Register message handler
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Register callback handler for buttons
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    # Register error handler
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
