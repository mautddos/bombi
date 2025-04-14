from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Dasi", callback_data='dasi')],
        [InlineKeyboardButton("Vidasi", callback_data='vidasi')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'dasi':
        keyboard = [
            [InlineKeyboardButton("Normal", callback_data='normal')],
            [InlineKeyboardButton("Leak", callback_data='leak')],
            [
                InlineKeyboardButton("Back", callback_data='back'),
                InlineKeyboardButton("Next", callback_data='next')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text="Dasi options:", reply_markup=reply_markup)
    elif query.data == 'vidasi':
        # Add similar functionality for Vidasi if needed
        pass
    elif query.data == 'back':
        # Go back to the main menu
        keyboard = [
            [InlineKeyboardButton("Dasi", callback_data='dasi')],
            [InlineKeyboardButton("Vidasi", callback_data='vidasi')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text='Please choose:', reply_markup=reply_markup)
    elif query.data == 'next':
        # Add functionality for next button
        query.edit_message_text(text="Next button pressed")
    elif query.data in ['normal', 'leak']:
        query.edit_message_text(text=f"You selected {query.data}")

def main() -> None:
    # Replace 'YOUR_TOKEN' with your actual bot token
    updater = Updater("8125880528:AAHRUQpcmN645oKmvjt8OeGSGVjG_9Aas38")

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
