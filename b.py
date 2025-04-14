import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, Filters
import subprocess
import os
import re
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(message)s', 
    level=logging.INFO,
    filename='bot_activity.log'  # Log all activity
)
logger = logging.getLogger(__name__)

TOKEN = "8125880528:AAEslZC6Bcgo79TisxS8v5cnuPElvbFG0FA"

# Safety Configuration
ALLOWED_DELETE_EXTENSIONS = ['.py', '.txt', '.log', '.json']
MAX_DELETE_SIZE = 1024 * 1024  # 1MB maximum file size

def safe_delete_path(path: str) -> bool:
    """Check if a path is safe to delete"""
    if not os.path.exists(path):
        return False
    
    # Prevent directory deletion
    if os.path.isdir(path):
        return False
    
    # Check file extension
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_DELETE_EXTENSIONS:
        return False
    
    # Check file size
    if os.path.getsize(path) > MAX_DELETE_SIZE:
        return False
    
    return True

def log_action(user: str, action: str, target: str):
    """Log all actions for audit"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {user} {action} {target}\n"
    with open('bot_actions.log', 'a') as f:
        f.write(log_entry)

# ... [keep all previous functions until main] ...

def delete_file(update: Update, context: CallbackContext) -> None:
    """Safely delete a file"""
    if not context.args:
        update.message.reply_text('ℹ️ Usage: /delete filename.ext')
        return
    
    filename = ' '.join(context.args)
    user = update.effective_user.username or str(update.effective_user.id)
    
    if not safe_delete_path(filename):
        update.message.reply_text(
            '❌ Deletion blocked. Reasons may include:\n'
            '- File does not exist\n'
            '- File is a directory\n'
            '- File type not allowed\n'
            '- File too large (>1MB)\n'
            f'Allowed extensions: {", ".join(ALLOWED_DELETE_EXTENSIONS)}'
        )
        return
    
    try:
        # Create backup first
        backup_name = f"{filename}.bak"
        os.rename(filename, backup_name)
        
        # Verify backup exists before deleting
        if os.path.exists(backup_name):
            os.remove(backup_name)
            log_action(user, "DELETED", filename)
            update.message.reply_text(f'✅ Deleted: {filename}')
        else:
            update.message.reply_text('❌ Backup verification failed. File not deleted.')
            
    except Exception as e:
        update.message.reply_text(f'❌ Deletion failed: {str(e)}')
        logger.error(f"Delete failed by {user}: {str(e)}")

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    # Existing handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("new", new_terminal))
    dispatcher.add_handler(CommandHandler("run", run_command))
    dispatcher.add_handler(CommandHandler("stop", stop_processes))
    dispatcher.add_handler(CommandHandler("gitclone", git_clone))
    
    # New delete handler
    dispatcher.add_handler(CommandHandler("delete", delete_file))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
