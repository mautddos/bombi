import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)

# Bot configuration with YOUR details
TOKEN = '7671101775:AAGsXtFQwbTUCooj9d9uPvwYZu1euS--6B4'
ADMIN_ID = 8167507955  # Your Telegram user ID
CHANNEL_ID = -1002651707544  # Your channel ID
CHANNEL_LINK = 'https://t.me/+t-tA66eXnv02NDE1'  # Your channel link
JOIN_CHANNEL_TEXT = "Please join our channel to use this bot:"
WELCOME_MESSAGE = "Welcome to Python Hosting Bot!\nUse /host to upload your Python file for hosting."

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Check if user is in channel
    try:
        member = context.bot.get_chat_member(CHANNEL_ID, user.id)
        if member.status in ['left', 'kicked']:
            # User is not in channel
            keyboard = [
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("I've Joined ✅", callback_data='check_join')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                f"{JOIN_CHANNEL_TEXT}",
                reply_markup=reply_markup
            )
            return
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        update.message.reply_text("There was an error verifying your channel membership. Please try again later.")
        return
    
    # User is in channel or is admin
    update.message.reply_text(WELCOME_MESSAGE)

def check_join_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = query.from_user
    
    try:
        member = context.bot.get_chat_member(CHANNEL_ID, user.id)
        if member.status in ['left', 'kicked']:
            query.answer("You haven't joined the channel yet! Click the 'Join Channel' button first.", show_alert=True)
        else:
            query.answer("Thank you for joining! You can now use the bot.", show_alert=True)
            query.edit_message_text(WELCOME_MESSAGE)
    except Exception as e:
        logger.error(f"Error in check_join_callback: {e}")
        query.answer("There was an error. Please try again.", show_alert=True)

def host_command(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    
    # Check channel membership first
    try:
        member = context.bot.get_chat_member(CHANNEL_ID, user.id)
        if member.status in ['left', 'kicked']:
            keyboard = [
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("I've Joined ✅", callback_data='check_join')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                f"You must join our channel to use this feature.\n{JOIN_CHANNEL_TEXT}",
                reply_markup=reply_markup
            )
            return
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        update.message.reply_text("There was an error verifying your channel membership. Please try again later.")
        return
    
    # If user is in channel
    update.message.reply_text("Please send me your Python (.py) file to host.\n\nNote: Files should be less than 20MB.")

def handle_document(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    document = update.message.document
    
    # Check if it's a Python file
    if not document.file_name.lower().endswith('.py'):
        update.message.reply_text("❌ Please send only Python files (.py extension).")
        return
    
    # Check file size (max 20MB)
    if document.file_size > 20 * 1024 * 1024:  # 20MB limit
        update.message.reply_text("❌ File too large. Maximum size is 20MB.")
        return
    
    # Check channel membership
    try:
        member = context.bot.get_chat_member(CHANNEL_ID, user.id)
        if member.status in ['left', 'kicked']:
            keyboard = [
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("I've Joined ✅", callback_data='check_join')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                f"You must join our channel to use this feature.\n{JOIN_CHANNEL_TEXT}",
                reply_markup=reply_markup
            )
            return
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        update.message.reply_text("There was an error verifying your channel membership. Please try again later.")
        return
    
    # Download the file
    file = context.bot.get_file(document.file_id)
    download_path = f"user_files/{user.id}_{document.file_name}"
    
    # Create user_files directory if it doesn't exist
    os.makedirs("user_files", exist_ok=True)
    
    try:
        file.download(download_path)
        
        # Respond to user
        update.message.reply_text(
            f"✅ File {document.file_name} received and hosted successfully!\n\n"
            f"File size: {round(document.file_size/1024, 2)} KB\n"
            f"Saved as: {download_path}"
        )
        
        # Notify admin
        context.bot.send_message(
            ADMIN_ID,
            f"📁 New file hosted by @{user.username or user.first_name} (ID: {user.id})\n"
            f"📝 File: {document.file_name}\n"
            f"💾 Size: {round(document.file_size/1024, 2)} KB"
        )
    except Exception as e:
        logger.error(f"Error handling file: {e}")
        update.message.reply_text("❌ There was an error processing your file. Please try again.")

def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # Notify admin
    context.bot.send_message(
        ADMIN_ID,
        f"⚠️ Error occurred:\n{context.error}\n\n"
        f"Update: {update.to_dict() if update else 'None'}"
    )

def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("host", host_command))
    
    # Register callback for join check button
    dispatcher.add_handler(CallbackQueryHandler(check_join_callback, pattern='^check_join$'))
    
    # Register document handler
    dispatcher.add_handler(MessageHandler(Filters.document, handle_document))
    
    # Register error handler
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    print("Bot is running...")
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
