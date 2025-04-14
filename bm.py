import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import subprocess
import os
import signal
import re

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8125880528:AAEslZC6Bcgo79TisxS8v5cnuPElvbFG0FA"

# Dictionary to store running processes
running_processes = {}

# List of restricted commands
RESTRICTED_COMMANDS = [
    'rm -rf',
    'chmod',
    'dd',
    'mv',
    ':(){:|:&};:',
    'mkfs',
    'shutdown',
    'reboot'
]

def is_command_allowed(command: str) -> bool:
    """Check if command contains restricted patterns"""
    command_lower = command.lower()
    return not any(
        restricted in command_lower 
        for restricted in RESTRICTED_COMMANDS
    )

def start(update: Update, context: CallbackContext) -> None:
    """Send welcome message"""
    update.message.reply_text(
        '🚀 Terminal Bot\n\n'
        '/new - Open new terminal\n'
        '/run <command> - Execute command\n'
        '/stop - Stop running processes\n'
        '/gitclone <url> - Safely clone git repo'
    )

def new_terminal(update: Update, context: CallbackContext) -> None:
    """Open new terminal session"""
    try:
        if os.name == 'posix':
            proc = subprocess.Popen(
                ['am', 'start', '--user', '0', '-n', 'com.termux/com.termux.app.TermuxActivity'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            running_processes[proc.pid] = proc
            update.message.reply_text('✅ New Termux session opened!')
        else:
            update.message.reply_text('⚠️ Only works on Termux (Android)')
    except Exception as e:
        update.message.reply_text(f'❌ Error: {str(e)}')

def run_command(update: Update, context: CallbackContext) -> None:
    """Execute command with safety checks"""
    if not context.args:
        update.message.reply_text('ℹ️ Usage: /run <command>')
        return
    
    command = ' '.join(context.args)
    
    if not is_command_allowed(command):
        update.message.reply_text('❌ Restricted command detected!')
        return
    
    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        running_processes[proc.pid] = proc
        
        stdout, stderr = proc.communicate(timeout=60)
        
        response = f"🔧 Command: {command}\n\n"
        response += f"📤 Exit Code: {proc.returncode}\n\n"
        
        if stdout:
            response += f"📄 Output:\n{stdout[:3000]}\n\n"
        if stderr:
            response += f"❌ Errors:\n{stderr[:1000]}"
        
        if len(response) > 4000:
            response = response[:4000] + "\n... (truncated)"
            
        update.message.reply_text(response)
        
    except subprocess.TimeoutExpired:
        proc.kill()
        update.message.reply_text(f"⏰ Command timed out: {command}")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        if proc.pid in running_processes:
            del running_processes[proc.pid]

def git_clone(update: Update, context: CallbackContext) -> None:
    """Safely handle git clone operations"""
    if not context.args:
        update.message.reply_text('ℹ️ Usage: /gitclone <repository_url>')
        return
    
    url = context.args[0]
    if not re.match(r'^https?://(github\.com|gitlab\.com|bitbucket\.org)/', url):
        update.message.reply_text('❌ Only GitHub/GitLab/BitBucket URLs allowed')
        return
    
    try:
        proc = subprocess.Popen(
            ['git', 'clone', url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        running_processes[proc.pid] = proc
        
        stdout, stderr = proc.communicate(timeout=300)
        
        response = f"🌐 Git Clone: {url}\n\n"
        if stdout:
            response += f"📄 Output:\n{stdout[:3000]}\n\n"
        if stderr:
            response += f"❌ Errors:\n{stderr[:1000]}"
            
        update.message.reply_text(response)
        
    except subprocess.TimeoutExpired:
        proc.kill()
        update.message.reply_text("⏰ Git clone timed out")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        if proc.pid in running_processes:
            del running_processes[proc.pid]

def stop_processes(update: Update, context: CallbackContext) -> None:
    """Stop all running processes"""
    if not running_processes:
        update.message.reply_text("ℹ️ No processes running")
        return
    
    count = 0
    for pid, proc in list(running_processes.items()):
        try:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
            count += 1
        except Exception as e:
            logger.error(f"Error stopping process {pid}: {e}")
        finally:
            if pid in running_processes:
                del running_processes[pid]
    
    update.message.reply_text(f"🛑 Stopped {count} processes")

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("new", new_terminal))
    dispatcher.add_handler(CommandHandler("run", run_command))
    dispatcher.add_handler(CommandHandler("stop", stop_processes))
    dispatcher.add_handler(CommandHandler("gitclone", git_clone))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
