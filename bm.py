import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import subprocess
import os
import signal

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your bot token
TOKEN = "8125880528:AAEslZC6Bcgo79TisxS8v5cnuPElvbFG0FA"

# Dictionary to store running processes
running_processes = {}

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        'Terminal Bot is running!\n'
        'Use /new to open a new terminal session\n'
        'Use /run <command> to execute a command directly\n'
        'Use /stop to terminate all running processes'
    )

def new_terminal(update: Update, context: CallbackContext) -> None:
    """Open a new terminal session"""
    try:
        # For Linux/Android (Termux)
        if os.name == 'posix':
            process = subprocess.Popen(['am', 'start', '--user', '0', '-n', 'com.termux/com.termux.app.TermuxActivity'])
            running_processes[process.pid] = process
            update.message.reply_text('New Termux session opened!')
        
        # For Windows
        elif os.name == 'nt':
            process = subprocess.Popen('start cmd', shell=True)
            running_processes[process.pid] = process
            update.message.reply_text('New CMD session opened!')
        
        # For MacOS
        else:
            process = subprocess.Popen(['open', '-a', 'Terminal'])
            running_processes[process.pid] = process
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
        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        running_processes[process.pid] = process
        
        # Wait for the process to complete with timeout
        try:
            stdout, stderr = process.communicate(timeout=15)
            output = f"Command: {command}\n\nExit Code: {process.returncode}\n\n"
            output += "STDOUT:\n" + (stdout if stdout else "<empty>") + "\n\n"
            output += "STDERR:\n" + (stderr if stderr else "<empty>")
            
            # Telegram has a 4096 character limit for messages
            if len(output) > 4000:
                output = output[:4000] + "\n\n... (output truncated)"
            
            update.message.reply_text(output)
        
        except subprocess.TimeoutExpired:
            process.kill()
            update.message.reply_text(f"Command timed out and was killed: {command}")
        
        # Remove the process from tracking
        if process.pid in running_processes:
            del running_processes[process.pid]
    
    except Exception as e:
        update.message.reply_text(f"Error executing command: {str(e)}")

def stop_processes(update: Update, context: CallbackContext) -> None:
    """Stop all running processes"""
    if not running_processes:
        update.message.reply_text("No processes are currently running")
        return
    
    count = 0
    for pid, process in list(running_processes.items()):
        try:
            # Try to terminate gracefully first
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                process.kill()
            
            count += 1
            del running_processes[pid]
        except Exception as e:
            update.message.reply_text(f"Error stopping process {pid}: {str(e)}")
    
    update.message.reply_text(f"Stopped {count} running processes")

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
    dispatcher.add_handler(CommandHandler("stop", stop_processes))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
