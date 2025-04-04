import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    CallbackQueryHandler,
    filters
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

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Check if user is in channel
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)
        if member.status in ['left', 'kicked']:
            # User is not in channel
            keyboard = [
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("I've Joined ✅", callback_data='check_join')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"{JOIN_CHANNEL_TEXT}",
                reply_markup=reply_markup
            )
            return
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        await update.message.reply_text("There was an error verifying your channel membership. Please try again later.")
        return
    
    # User is in channel or is admin
    await update.message.reply_text(WELCOME_MESSAGE)

async def check_join_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = query.from_user
    
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)
        if member.status in ['left', 'kicked']:
            await query.answer("You haven't joined the channel yet! Click the 'Join Channel' button first.", show_alert=True)
        else:
            await query.answer("Thank you for joining! You can now use the bot.", show_alert=True)
            await query.edit_message_text(WELCOME_MESSAGE)
    except Exception as e:
        logger.error(f"Error in check_join_callback: {e}")
        await query.answer("There was an error. Please try again.", show_alert=True)

async def host_command(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    
    # Check channel membership first
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)
        if member.status in ['left', 'kicked']:
            keyboard = [
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("I've Joined ✅", callback_data='check_join')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"You must join our channel to use this feature.\n{JOIN_CHANNEL_TEXT}",
                reply_markup=reply_markup
            )
            return
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        await update.message.reply_text("There was an error verifying your channel membership. Please try again later.")
        return
    
    # If user is in channel
    await update.message.reply_text("Please send me your Python (.py) file to host.\n\nNote: Files should be less than 20MB.")

async def handle_document(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    document = update.message.document
    
    # Check if it's a Python file
    if not document.file_name.lower().endswith('.py'):
        await update.message.reply_text("❌ Please send only Python files (.py extension).")
        return
    
    # Check file size (max 20MB)
    if document.file_size > 20 * 1024 * 1024:  # 20MB limit
        await update.message.reply_text("❌ File too large. Maximum size is 20MB.")
        return
    
    # Check channel membership
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)
        if member.status in ['left', 'kicked']:
            keyboard = [
                [InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("I've Joined ✅", callback_data='check_join')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"You must join our channel to use this feature.\n{JOIN_CHANNEL_TEXT}",
                reply_markup=reply_markup
            )
            return
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        await update.message.reply_text("There was an error verifying your channel membership. Please try again later.")
        return
    
    # Download the file
    file = await context.bot.get_file(document.file_id)
    download_path = f"user_files/{user.id}_{document.file_name}"
    
    # Create user_files directory if it doesn't exist
    os.makedirs("user_files", exist_ok=True)
    
    try:
        await file.download_to_drive(download_path)
        
        # Respond to user
        await update.message.reply_text(
            f"✅ File {document.file_name} received and hosted successfully!\n\n"
            f"File size: {round(document.file_size/1024, 2)} KB\n"
            f"Saved as: {download_path}"
        )
        
        # Notify admin
        await context.bot.send_message(
            ADMIN_ID,
            f"📁 New file hosted by @{user.username or user.first_name} (ID: {user.id})\n"
            f"📝 File: {document.file_name}\n"
            f"💾 Size: {round(document.file_size/1024, 2)} KB"
        )
    except Exception as e:
        logger.error(f"Error handling file: {e}")
        await update.message.reply_text("❌ There was an error processing your file. Please try again.")

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # Notify admin
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"⚠️ Error occurred:\n{context.error}\n\n"
            f"Update: {update.to_dict() if update else 'None'}"
        )
    except Exception as e:
        logger.error(f"Error sending error notification: {e}")

def main() -> None:
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Register commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("host", host_command))
    
    # Register callback for join check button
    application.add_handler(CallbackQueryHandler(check_join_callback, pattern='^check_join$'))
    
    # Register document handler
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Register error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
