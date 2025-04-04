import logging
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ParseMode,
    ChatPermissions
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
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

# Bot token from BotFather
TOKEN = "8100391327:AAHTBZ6WGBNpVtnj7uiZRAbGuEF7xbK9THs"

# Conversation states
MAIN_MENU, WELCOME_SETTINGS, ADMIN_TOOLS, FUN_COMMANDS = range(4)

# Admin commands that require admin privileges
ADMIN_COMMANDS = ['ban', 'mute', 'warn', 'kick', 'purge', 'pin', 'unpin']

# User warnings storage (in a real bot, use a database)
user_warnings = {}

# Jokes, quotes, facts databases
JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them.",
    "Why don't skeletons fight each other? They don't have the guts.",
]

QUOTES = [
    "The only way to do great work is to love what you do. - Steve Jobs",
    "Innovation distinguishes between a leader and a follower. - Steve Jobs",
    "Your time is limited, don't waste it living someone else's life. - Steve Jobs",
]

FACTS = [
    "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat.",
    "Octopuses have three hearts, nine brains, and blue blood.",
    "The shortest war in history was between Britain and Zanzibar on August 27, 1896. Zanzibar surrendered after 38 minutes.",
]

def start(update: Update, context: CallbackContext) -> int:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    keyboard = [
        [
            InlineKeyboardButton("⚙️ Welcome Settings", callback_data=str(WELCOME_SETTINGS)),
            InlineKeyboardButton("🛡️ Admin Tools", callback_data=str(ADMIN_TOOLS)),
        ],
        [InlineKeyboardButton("🎉 Fun Commands", callback_data=str(FUN_COMMANDS))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_html(
        rf"👋 Hi {user.mention_html()}! I'm your advanced group management bot.\n\n"
        "I can help you manage your group with powerful tools and entertain your members!",
        reply_markup=reply_markup,
    )
    return MAIN_MENU

def main_menu(update: Update, context: CallbackContext) -> int:
    """Return to main menu."""
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("⚙️ Welcome Settings", callback_data=str(WELCOME_SETTINGS)),
            InlineKeyboardButton("🛡️ Admin Tools", callback_data=str(ADMIN_TOOLS)),
        ],
        [InlineKeyboardButton("🎉 Fun Commands", callback_data=str(FUN_COMMANDS))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        text="🏠 Main Menu\n\nWhat would you like to do?",
        reply_markup=reply_markup,
    )
    return MAIN_MENU

def welcome_settings_menu(update: Update, context: CallbackContext) -> int:
    """Show welcome settings options."""
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("📝 Set Welcome Message", callback_data="set_welcome"),
            InlineKeyboardButton("👋 Set Goodbye Message", callback_data="set_goodbye"),
        ],
        [
            InlineKeyboardButton("🖼️ Set Welcome Image", callback_data="set_welcome_image"),
            InlineKeyboardButton("📊 Welcome Stats", callback_data="welcome_stats"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        text="⚙️ Welcome Message Settings\n\nConfigure how I welcome new members to your group.",
        reply_markup=reply_markup,
    )
    return WELCOME_SETTINGS

def admin_tools_menu(update: Update, context: CallbackContext) -> int:
    """Show admin tools."""
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("🔨 Ban User", callback_data="ban_menu"),
            InlineKeyboardButton("🔇 Mute User", callback_data="mute_menu"),
        ],
        [
            InlineKeyboardButton("⚠️ Warn User", callback_data="warn_menu"),
            InlineKeyboardButton("👢 Kick User", callback_data="kick_menu"),
        ],
        [
            InlineKeyboardButton("🧹 Purge Messages", callback_data="purge_menu"),
            InlineKeyboardButton("📌 Pin Message", callback_data="pin_menu"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        text="🛡️ Admin Tools\n\nManage your group with these powerful moderation tools.",
        reply_markup=reply_markup,
    )
    return ADMIN_TOOLS

def fun_commands_menu(update: Update, context: CallbackContext) -> int:
    """Show fun commands."""
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("😂 Random Joke", callback_data="random_joke"),
            InlineKeyboardButton("💬 Random Quote", callback_data="random_quote"),
        ],
        [
            InlineKeyboardButton("📚 Random Fact", callback_data="random_fact"),
            InlineKeyboardButton("🎲 Random Number", callback_data="random_number"),
        ],
        [
            InlineKeyboardButton("🐶 Random Dog", callback_data="random_dog"),
            InlineKeyboardButton("🐱 Random Cat", callback_data="random_cat"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        text="🎉 Fun Commands\n\nLet's have some fun with these commands!",
        reply_markup=reply_markup,
    )
    return FUN_COMMANDS

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a help message."""
    help_text = """
    🤖 *Bot Commands Help*:

    *Group Management:*
    /start - Start interacting with the bot
    /help - Show this help message
    /welcome - Configure welcome messages
    /rules - Set group rules
    /report - Report a user to admins

    *Admin Commands:*
    /ban - Ban a user
    /mute - Mute a user
    /warn - Warn a user
    /kick - Kick a user
    /purge - Delete multiple messages
    /pin - Pin a message
    /unpin - Unpin a message
    /promote - Promote a user to admin
    /demote - Demote an admin

    *Fun Commands:*
    /joke - Get a random joke
    /quote - Get an inspirational quote
    /fact - Get an interesting fact
    /roll - Roll a dice
    /flip - Flip a coin
    /dog - Get a random dog picture
    /cat - Get a random cat picture

    *Utility Commands:*
    /id - Get user/group ID
    /info - Get user info
    /time - Get current time
    /weather - Get weather info
    """
    update.message.reply_text(help_text, parse_mode="Markdown")

# Admin commands implementation
def ban_user(update: Update, context: CallbackContext) -> None:
    """Ban a user from the group."""
    if not is_user_admin(update, context):
        update.message.reply_text("You need to be an admin to use this command.")
        return

    if not context.args:
        update.message.reply_text("Please specify a user to ban (reply or user ID).")
        return

    try:
        user_id = int(context.args[0])
        context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id
        )
        update.message.reply_text(f"User {user_id} has been banned.")
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

def mute_user(update: Update, context: CallbackContext) -> None:
    """Mute a user in the group."""
    if not is_user_admin(update, context):
        update.message.reply_text("You need to be an admin to use this command.")
        return

    if not context.args:
        update.message.reply_text("Please specify a user to mute (reply or user ID) and optional time (e.g., 1h, 30m).")
        return

    try:
        user_id = int(context.args[0])
        until_date = datetime.now() + timedelta(hours=1)  # Default 1 hour mute
        
        if len(context.args) > 1:
            time_arg = context.args[1].lower()
            if 'h' in time_arg:
                hours = int(time_arg.replace('h', ''))
                until_date = datetime.now() + timedelta(hours=hours)
            elif 'm' in time_arg:
                minutes = int(time_arg.replace('m', ''))
                until_date = datetime.now() + timedelta(minutes=minutes)
            elif 'd' in time_arg:
                days = int(time_arg.replace('d', ''))
                until_date = datetime.now() + timedelta(days=days)

        context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            ),
            until_date=until_date
        )
        update.message.reply_text(f"User {user_id} has been muted until {until_date}.")
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

def warn_user(update: Update, context: CallbackContext) -> None:
    """Warn a user and take action if warnings exceed limit."""
    if not is_user_admin(update, context):
        update.message.reply_text("You need to be an admin to use this command.")
        return

    if not context.args:
        update.message.reply_text("Please specify a user to warn (reply or user ID).")
        return

    try:
        user_id = int(context.args[0])
        chat_id = update.effective_chat.id
        
        # Initialize warnings for this chat if not exists
        if chat_id not in user_warnings:
            user_warnings[chat_id] = {}
        
        # Increment warning count
        if user_id in user_warnings[chat_id]:
            user_warnings[chat_id][user_id] += 1
        else:
            user_warnings[chat_id][user_id] = 1
        
        warning_count = user_warnings[chat_id][user_id]
        
        if warning_count >= 3:  # 3 warnings = ban
            context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            del user_warnings[chat_id][user_id]  # Reset warnings
            update.message.reply_text(
                f"User {user_id} has reached 3 warnings and has been banned."
            )
        else:
            update.message.reply_text(
                f"User {user_id} has been warned. ({warning_count}/3 warnings)"
            )
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

def purge_messages(update: Update, context: CallbackContext) -> None:
    """Delete multiple messages at once."""
    if not is_user_admin(update, context):
        update.message.reply_text("You need to be an admin to use this command.")
        return

    if not context.args:
        update.message.reply_text("Please specify how many messages to delete (e.g., /purge 10).")
        return

    try:
        count = int(context.args[0]) + 1  # +1 to include the command message
        if count > 100:
            update.message.reply_text("You can only delete up to 100 messages at once.")
            return

        message_id = update.message.message_id
        chat_id = update.effective_chat.id
        
        # Delete messages in batches
        for i in range(message_id, message_id - count, -1):
            try:
                context.bot.delete_message(chat_id=chat_id, message_id=i)
            except Exception:
                continue  # Skip if message can't be deleted
        
        update.message.reply_text(f"Purged {count-1} messages.")
    except Exception as e:
        update.message.reply_text(f"Error: {str(e)}")

# Fun commands implementation
def random_joke(update: Update, context: CallbackContext) -> None:
    """Send a random joke."""
    joke = random.choice(JOKES)
    update.message.reply_text(joke)

def random_quote(update: Update, context: CallbackContext) -> None:
    """Send a random quote."""
    quote = random.choice(QUOTES)
    update.message.reply_text(quote)

def random_fact(update: Update, context: CallbackContext) -> None:
    """Send a random fact."""
    fact = random.choice(FACTS)
    update.message.reply_text(f"Did you know?\n\n{fact}")

def random_dog(update: Update, context: CallbackContext) -> None:
    """Send a random dog picture."""
    try:
        response = requests.get("https://dog.ceo/api/breeds/image/random")
        if response.status_code == 200:
            image_url = response.json()["message"]
            context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_url,
                caption="Here's a random dog for you! 🐶"
            )
    except Exception as e:
        update.message.reply_text("Couldn't fetch a dog picture. Try again later.")

def random_cat(update: Update, context: CallbackContext) -> None:
    """Send a random cat picture."""
    try:
        response = requests.get("https://api.thecatapi.com/v1/images/search")
        if response.status_code == 200:
            image_url = response.json()[0]["url"]
            context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_url,
                caption="Here's a random cat for you! 🐱"
            )
    except Exception as e:
        update.message.reply_text("Couldn't fetch a cat picture. Try again later.")

# Utility commands
def get_user_id(update: Update, context: CallbackContext) -> None:
    """Get the user's ID or chat ID."""
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        update.message.reply_text(f"User ID: {user.id}")
    else:
        update.message.reply_text(f"Your ID: {update.effective_user.id}\nChat ID: {update.effective_chat.id}")

def get_user_info(update: Update, context: CallbackContext) -> None:
    """Get information about a user."""
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    else:
        user = update.effective_user

    info_text = f"""
    👤 *User Information*:
    
    *Name:* {user.full_name}
    *Username:* @{user.username if user.username else 'N/A'}
    *ID:* `{user.id}`
    *Profile Link:* [Link](tg://user?id={user.id})
    """
    update.message.reply_text(info_text, parse_mode="Markdown")

def get_current_time(update: Update, context: CallbackContext) -> None:
    """Get the current time."""
    now = datetime.now()
    update.message.reply_text(f"⏰ Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# Helper functions
def is_user_admin(update: Update, context: CallbackContext) -> bool:
    """Check if the user is an admin in the chat."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if user is chat admin
    admins = context.bot.get_chat_administrators(chat.id)
    admin_ids = [admin.user.id for admin in admins]
    
    return user.id in admin_ids

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log errors and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update and update.effective_message:
        update.effective_message.reply_text(
            "An error occurred while processing your request. Please try again later."
        )

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(welcome_settings_menu, pattern='^' + str(WELCOME_SETTINGS) + '$'),
                CallbackQueryHandler(admin_tools_menu, pattern='^' + str(ADMIN_TOOLS) + '$'),
                CallbackQueryHandler(fun_commands_menu, pattern='^' + str(FUN_COMMANDS) + '$'),
                CallbackQueryHandler(main_menu, pattern='^back$'),
            ],
            WELCOME_SETTINGS: [
                CallbackQueryHandler(main_menu, pattern='^back$'),
            ],
            ADMIN_TOOLS: [
                CallbackQueryHandler(main_menu, pattern='^back$'),
            ],
            FUN_COMMANDS: [
                CallbackQueryHandler(main_menu, pattern='^back$'),
                CallbackQueryHandler(random_joke, pattern='^random_joke$'),
                CallbackQueryHandler(random_quote, pattern='^random_quote$'),
                CallbackQueryHandler(random_fact, pattern='^random_fact$'),
                CallbackQueryHandler(random_dog, pattern='^random_dog$'),
                CallbackQueryHandler(random_cat, pattern='^random_cat$'),
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    dispatcher.add_handler(conv_handler)
    
    # Command handlers
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Admin commands
    dispatcher.add_handler(CommandHandler("ban", ban_user))
    dispatcher.add_handler(CommandHandler("mute", mute_user))
    dispatcher.add_handler(CommandHandler("warn", warn_user))
    dispatcher.add_handler(CommandHandler("purge", purge_messages))
    
    # Fun commands
    dispatcher.add_handler(CommandHandler("joke", random_joke))
    dispatcher.add_handler(CommandHandler("quote", random_quote))
    dispatcher.add_handler(CommandHandler("fact", random_fact))
    dispatcher.add_handler(CommandHandler("dog", random_dog))
    dispatcher.add_handler(CommandHandler("cat", random_cat))
    
    # Utility commands
    dispatcher.add_handler(CommandHandler("id", get_user_id))
    dispatcher.add_handler(CommandHandler("info", get_user_info))
    dispatcher.add_handler(CommandHandler("time", get_current_time))
    
    # Register error handler
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
