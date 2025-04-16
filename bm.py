import random
import os
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, CallbackContext

# Configuration
TOKEN = "7305528493:AAEMfj04SCLS0Mtpf0llZolpkkB3CHKSDK4"
MAX_PROXIES_PER_REQUEST = 100000  # Safety limit to prevent abuse

def generate_proxy():
    """Generate a single random proxy in the format IP:PORT"""
    ip = ".".join(str(random.randint(1, 255)) for _ in range(4))
    port = random.choice([80, 1080, 3128, 8080])  # Common proxy ports
    return f"{ip}:{port}"

def generate_unique_proxies(count):
    """Generate a set of unique proxies"""
    proxies = set()
    while len(proxies) < count:
        proxies.add(generate_proxy())
        # Prevent infinite loops if asking for more than possible unique combinations
        if len(proxies) > 1000000:
            break
    return proxies

def gen_command(update: Update, context: CallbackContext) -> None:
    """Handle the /gen command"""
    try:
        # Get the count from command arguments
        if not context.args:
            update.message.reply_text("Please specify the number of proxies to generate. Example: /gen 10")
            return
            
        count = int(context.args[0])
        
        # Validate the count
        if count <= 0:
            update.message.reply_text("Please specify a positive number.")
            return
            
        if count > MAX_PROXIES_PER_REQUEST:
            update.message.reply_text(f"Maximum {MAX_PROXIES_PER_REQUEST} proxies per request allowed.")
            count = MAX_PROXIES_PER_REQUEST
            
        # Generate proxies
        proxies = generate_unique_proxies(count)
        
        # Create a temporary file
        filename = f"proxies_{count}.txt"
        with open(filename, 'w') as f:
            f.write("\n".join(proxies))
        
        # Send the file
        with open(filename, 'rb') as f:
            update.message.reply_document(
                document=InputFile(f, filename=filename),
                caption=f"Here are your {len(proxies)} unique proxies!"
            )
        
        # Clean up
        os.remove(filename)
        
    except ValueError:
        update.message.reply_text("Please provide a valid number. Example: /gen 10")
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register commands
    dispatcher.add_handler(CommandHandler("gen", gen_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
