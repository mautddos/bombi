import logging
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ChatPermissions,
    ChatMemberAdministrator
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler
)
import random
import requests
from datetime import datetime, timedelta

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = "8100391327:AAHTBZ6WGBNpVtnj7uiZRAbGuEF7xbK9THs"

# Conversation states
MAIN_MENU, WELCOME_SETTINGS, ADMIN_TOOLS, FUN_COMMANDS = range(4)

# User warnings storage
user_warnings = {}

# Jokes, quotes, facts databases
JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    # ... (keep your existing jokes)
]

# ... (keep your existing QUOTES and FACTS)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a welcome message when the command /start is issued."""
    # ... (keep your existing start function)

# ... (keep all your existing menu functions)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    help_text = """
    🤖 *Bot Commands Help*:

    *Admin Commands:*
    /ban [user_id] - Ban a user
    /unban [user_id] - Unban a user
    /mute [user_id] [time] - Mute a user (e.g., /mute 123456 1h)
    /unmute [user_id] - Unmute a user
    /warn [user_id] - Warn a user (3 warnings = ban)
    /kick [user_id] - Kick a user
    /purge [number] - Delete multiple messages
    /pin - Pin a message (reply to message)
    /unpin - Unpin a message
    /promote [user_id] - Promote a user to admin
    /demote [user_id] - Demote an admin
    
    *Fun Commands:*
    /joke - Get a random joke
    /quote - Get an inspirational quote
    /fact - Get an interesting fact
    /dog - Get a random dog picture
    /cat - Get a random cat picture
    
    *Utility Commands:*
    /id - Get user/group ID
    /info - Get user info
    /time - Get current time
    """
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# ADMIN COMMANDS IMPLEMENTATION

async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kick a user from the group."""
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You need to be an admin to use this command.")
        return

    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /kick [user_id] or reply to user's message with /kick")
        return

    try:
        user_id = int(context.args[0])
        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id
        )
        await context.bot.unban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id
        )
        await update.message.reply_text(f"✅ User {user_id} has been kicked.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def pin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pin a message in the chat."""
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You need to be an admin to use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("ℹ️ Please reply to a message to pin it.")
        return

    try:
        message_id = update.message.reply_to_message.message_id
        await context.bot.pin_chat_message(
            chat_id=update.effective_chat.id,
            message_id=message_id,
            disable_notification=True
        )
        await update.message.reply_text("✅ Message pinned successfully!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def unpin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unpin a message in the chat."""
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You need to be an admin to use this command.")
        return

    try:
        await context.bot.unpin_chat_message(
            chat_id=update.effective_chat.id
        )
        await update.message.reply_text("✅ Message unpinned successfully!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def promote_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Promote a user to admin."""
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You need to be an admin to use this command.")
        return

    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /promote [user_id]")
        return

    try:
        user_id = int(context.args[0])
        await context.bot.promote_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_restrict_members=True,
            can_promote_members=False,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True
        )
        await update.message.reply_text(f"✅ User {user_id} has been promoted to admin!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def demote_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Demote an admin."""
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You need to be an admin to use this command.")
        return

    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /demote [user_id]")
        return

    try:
        user_id = int(context.args[0])
        await context.bot.promote_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id,
            is_anonymous=False,
            can_manage_chat=False,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_promote_members=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        await update.message.reply_text(f"✅ User {user_id} has been demoted!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# ... (keep all your existing utility and fun commands)

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin in the chat."""
    user = update.effective_user
    chat = update.effective_chat
    
    if user.id == 1087968824:  # GroupAnonymousBot
        return True
    
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        # ... (keep your existing conversation handler setup)
    )
    application.add_handler(conv_handler)
    
    # Command handlers
    application.add_handler(CommandHandler("help", help_command))
    
    # Admin commands
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("kick", kick_user))
    application.add_handler(CommandHandler("purge", purge_messages))
    application.add_handler(CommandHandler("pin", pin_message))
    application.add_handler(CommandHandler("unpin", unpin_message))
    application.add_handler(CommandHandler("promote", promote_user))
    application.add_handler(CommandHandler("demote", demote_user))
    
    # Fun commands
    application.add_handler(CommandHandler("joke", random_joke))
    application.add_handler(CommandHandler("quote", random_quote))
    application.add_handler(CommandHandler("fact", random_fact))
    application.add_handler(CommandHandler("dog", random_dog))
    application.add_handler(CommandHandler("cat", random_cat))
    
    # Utility commands
    application.add_handler(CommandHandler("id", get_user_id))
    application.add_handler(CommandHandler("info", get_user_info))
    application.add_handler(CommandHandler("time", get_current_time))
    
    # Error handler
    application.add_error_handler(error_handler)

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
