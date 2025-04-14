import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import subprocess
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your bot token
TOKEN = "8125880528:AAEslZC6Bcgo79TisxS8v5cnuPElvbFG0FA"

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        'Terminal Bot is running!\n'
        'Use /new to open a new terminal session\n'
        'Use /run <command> to execute a command directly'
    )

def new_terminal(update: Update, context: CallbackContext) -> None:
    """Open a new terminal session"""
    try:
        # For Linux/Android (Termux)
        if os.name == 'posix':
            subprocess.Popen(['am', 'start', '--user', '0', '-n', 'com.termux/com.termux.app.TermuxActivity'])
            update.message.reply_text('New Termux session opened!')
        
        # For Windows
        elif os.name == 'nt':
            subprocess.Popen('start cmd', shell=True)
            update.message.reply_text('New CMD session opened!')
        
        # For MacOS
        else:
            subprocess.Popen(['open', '-a', 'Terminal'])
            update.message.reply_text('New Terminal session opened!')
    
    except Exception as e:
        update.message.reply_text(f'Error opening terminal: {str(e)}')

def run_command(update: Update, context: CallbackContext) -> None:
    """Execute a command directly"""
    if not context.args:
        update.message.reply_text('Please provide a command to run. Example: /run ls -la')
        return
    
    command = ' '.join(context.args)
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=15  # Safety timeout
        )
        
        output = f"Command: {command}\n\nExit Code: {result.returncode}\n\n"
        output += "STDOUT:\n" + (result.stdout if result.stdout else "<empty>") + "\n\n"
        output += "STDERR:\n" + (result.stderr if result.stderr else "<empty>")
        
        # Telegram has a 4096 character limit for messages
        if len(output) > 4000:
            output = output[:4000] + "\n\n... (output truncated)"
        
        update.message.reply_text(output)
    
    except subprocess.TimeoutExpired:
        update.message.reply_text(f"Command timed out: {command}")
    except Exception as e:
        update.message.reply_text(f"Error executing command: {str(e)}")

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("new", new_terminal))
    dispatcher.add_handler(CommandHandler("run", run_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main().
