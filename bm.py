from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

BOT_TOKEN = "8125880528:AAHRUQpcmN645oKmvjt8OeGSGVjG_9Aas38"
CHANNEL_ID = -1002441094491

# Store user progress
user_progress = {}

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Videos", callback_data='videos')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        update.message.reply_text('Click the button to get videos:', reply_markup=reply_markup)
    else:
        update.callback_query.edit_message_text('Click the button to get videos:', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    if query.data == 'videos':
        # Initialize or reset user progress
        user_progress[user_id] = {'last_sent': 0}
        send_batch(user_id, query)
    
    elif query.data == 'next':
        send_batch(user_id, query)

def send_batch(user_id, query):
    if user_id not in user_progress:
        user_progress[user_id] = {'last_sent': 0}
    
    start_msg = user_progress[user_id]['last_sent']
    end_msg = start_msg + 10
    sent_count = 0
    
    for msg_id in range(start_msg + 1, end_msg + 1):
        try:
            query.bot.copy_message(
                chat_id=query.message.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id
            )
            sent_count += 1
        except Exception as e:
            print(f"Failed to copy message {msg_id}: {e}")
    
    if sent_count > 0:
        user_progress[user_id]['last_sent'] = end_msg
        
        # Add Next button
        keyboard = [[InlineKeyboardButton("Next", callback_data='next')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.bot.send_message(
            chat_id=query.message.chat.id,
            text=f"Sent {sent_count} videos. Last sent ID: {end_msg}",
            reply_markup=reply_markup
        )
    else:
        query.bot.send_message(
            chat_id=query.message.chat.id,
            text="No more videos available or failed to send."
        )

def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
