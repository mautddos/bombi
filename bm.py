from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8125880528:AAHRUQpcmN645oKmvjt8OeGSGVjG_9Aas38"
CHANNEL_ID = -1002441094491  # Channel where videos are stored
VERIFICATION_CHANNEL_ID = -1002363906868  # Channel users must join
CHANNEL_USERNAME = "seedhe_maut"  # Without @ symbol
START_IMAGE_URL = "https://t.me/botstomp/125"  # Image for /start command

# Store user progress
user_progress = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Simplified welcome message without Markdown
    welcome_text = """
🎬 Welcome to Video Bot! 🎬

Here you can get access to our exclusive video collection.

Please join our channel first to use this bot:
@seedhe_maut
"""
    
    # Create buttons
    keyboard = [
        [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton("✅ I've Joined", callback_data='check_join')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # First send the image
    await update.message.reply_photo(
        photo=START_IMAGE_URL,
        caption=welcome_text,
        reply_markup=reply_markup,
        parse_mode=None  # Disable Markdown parsing
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'check_join':
        try:
            chat_member = await context.bot.get_chat_member(VERIFICATION_CHANNEL_ID, user_id)
            if chat_member.status in ['member', 'administrator', 'creator']:
                keyboard = [[InlineKeyboardButton("Get Videos", callback_data='videos')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    text="Thanks for joining! Click below to get videos:",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(text="Please join the channel first to access videos.")
        except Exception as e:
            print(f"Error checking membership: {e}")
            await query.edit_message_text(text="Couldn't verify your channel membership. Please try again.")
    
    elif query.data == 'videos':
        user_progress[user_id] = {'last_sent': 0}
        await send_batch(context.bot, user_id, query.message.chat.id)
    
    elif query.data == 'next':
        await send_batch(context.bot, user_id, query.message.chat.id)

async def send_batch(bot, user_id, chat_id):
    if user_id not in user_progress:
        user_progress[user_id] = {'last_sent': 0}
    
    start_msg = user_progress[user_id]['last_sent']
    end_msg = start_msg + 10
    sent_count = 0
    
    for msg_id in range(start_msg + 1, end_msg + 1):
        try:
            await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id
            )
            sent_count += 1
        except Exception as e:
            print(f"Failed to copy message {msg_id}: {e}")
    
    if sent_count > 0:
        user_progress[user_id]['last_sent'] = end_msg
        keyboard = [[InlineKeyboardButton("Next", callback_data='next')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(
            chat_id=chat_id,
            text=f"Sent {sent_count} videos. Last sent ID: {end_msg}",
            reply_markup=reply_markup
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text="No more videos available or failed to send."
        )

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == '__main__':
    main()
