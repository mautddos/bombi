import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import subprocess
import os
import re
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot_activity.log'
)
logger = logging.getLogger(__name__)

# Your bot token
TOKEN = "8125880528:AAEslZC6Bcgo79TisxS8v5cnuPElvbFG0FA"

# Dictionary to store running processes
running_processes = {}

# Safety Configuration
ALLOWED_DELETE_EXTENSIONS = ['.py', '.txt', '.log', '.json']
MAX_DELETE_SIZE = 1024 * 1024  # 1MB maximum file size

def safe_delete_path(path: str) -> bool:
    """Check if a path is safe to delete"""
    if not os.path.exists(path):
        return False
    if os.path.isdir(path):
        return False
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_DELETE_EXTENSIONS:
        return False
    if os.path.getsize(path) > MAX_DELETE_SIZE:
        return False
    return True

def log_action(user: str, action: str, target: str):
    """Log all actions for audit"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {user} {action} {target}\n"
    with open('bot_actions.log', 'a') as f:
        f.write(log_entry)

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        '🚀 Terminal Bot\n\n'
        'Available commands:\n'
        '/start - Show this message\n'
        '/new - Open new terminal\n'
        '/run <command> - Execute command\n'
        '/delete <file> - Delete a file\n'
        '/gitclone <url> - Clone a git repo\n'
        '/stop - Stop running processes'
    )

def new_terminal(update: Update, context: CallbackContext) -> None:
    """Open a new terminal session"""
    try:
        if os.name == 'posix':
            process = subprocess.Popen(['am', 'start', '--user', '0', '-n', 'com.termux/com.termux.app.TermuxActivity'])
            running_processes[process.pid] = process
            update.message.reply_text('✅ New Termux session opened!')
        else:
            update.message.reply_text('⚠️ Only works on Termux (Android)')
    except Exception as e:
        update.message.reply_text(f'❌ Error: {str(e)}')

def run_command(update: Update, context: CallbackContext) -> None:
    """Execute a command directly"""
    if not context.args:
        update.message.reply_text('ℹ️ Usage: /run <command>')
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
        
        stdout, stderr = process.communicate(timeout=60)
        
        response = f"🔧 Command: {command}\n\n"
        response += f"📤 Exit Code: {process.returncode}\n\n"
        
        if stdout:
            response += f"📄 Output:\n{stdout[:3000]}\n\n"
        if stderr:
            response += f"❌ Errors:\n{stderr[:1000]}"
        
        if len(response) > 4000:
            response = response[:4000] + "\n... (truncated)"
            
        update.message.reply_text(response)
        
    except subprocess.TimeoutExpired:
        process.kill()
        update.message.reply_text(f"⏰ Command timed out: {command}")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        if process.pid in running_processes:
            del running_processes[process.pid]

def git_clone(update: Update, context: CallbackContext) -> None:
    """Clone a git repository"""
    if not context.args:
        update.message.reply_text('ℹ️ Usage: /gitclone <repository_url>')
        return
    
    url = context.args[0]
    if not re.match(r'^https?://(github\.com|gitlab\.com|bitbucket\.org)/', url):
        update.message.reply_text('❌ Only GitHub/GitLab/BitBucket URLs allowed')
        return
    
    try:
        process = subprocess.Popen(
            ['git', 'clone', url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        running_processes[process.pid] = process
        
        stdout, stderr = process.communicate(timeout=300)
        
        response = f"🌐 Git Clone: {url}\n\n"
        if stdout:
            response += f"📄 Output:\n{stdout[:3000]}\n\n"
        if stderr:
            response += f"❌ Errors:\n{stderr[:1000]}"
            
        update.message.reply_text(response)
        
    except subprocess.TimeoutExpired:
        process.kill()
        update.message.reply_text("⏰ Git clone timed out")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        if process.pid in running_processes:
            del running_processes[process.pid]

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

def stop_processes(update: Update, context: CallbackContext) -> None:
    """Stop all running processes"""
    if not running_processes:
        update.message.reply_text("ℹ️ No processes running")
        return
    
    count = 0
    for pid, process in list(running_processes.items()):
        try:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
            count += 1
        except Exception as e:
            logger.error(f"Error stopping process {pid}: {e}")
        finally:
            if pid in running_processes:
                del running_processes[pid]
    
    update.message.reply_text(f"🛑 Stopped {count} processes")

def main() -> None:
    """Start the bot."""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("new", new_terminal))
    dispatcher.add_handler(CommandHandler("run", run_command))
    dispatcher.add_handler(CommandHandler("delete", delete_file))
    dispatcher.add_handler(CommandHandler("gitclone", git_clone))
    dispatcher.add_handler(CommandHandler("stop", stop_processes))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
