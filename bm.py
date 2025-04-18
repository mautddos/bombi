import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
import datetime
import time
import os

# Bot Configuration
BOT_TOKEN = "8125880528:AAHRUQpcmN645oKmvjt8OeGSGVjG_9Aas38"
CHANNEL_ID = -1001234567890  # Your channel ID with videos
VERIFICATION_CHANNEL = -1001234567891  # Channel user must join
ADMIN_ID = 8167507955  # Your admin ID

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store user progress
user_data = {}
blocked_users = set()

# Hindi texts with sexy language
WELCOME_TEXT = """
🔥 *ख़्वाहिशों का राज़ बॉट में आपका स्वागत है!* 🔥

💋 यहाँ मिलेगा:
✅ गर्मागर्म भारतीय कंटेंट
✅ प्राइवेट सेक्सी वीडियो
✅ वो सब कुछ जो आपकी रातों को गर्म कर दे

📛 *नियम:* 
1. पहले हमारे चैनल को ज्वाइन करें
2. वेरीफाई करें
3. वीडियो का मजा लें

👇 नीचे बटन दबाकर चैनल ज्वाइन करें और अपनी इच्छाओं को आजाद करें!
"""

VERIFIED_TEXT = """
💦 *वेरीफाई हो गया! अब तुम्हारी बारी है...* 💦

अनलॉक हुआ:
🥵 100+ प्राइवेट वीडियो
🍑 गुप्त कलेक्शन
🔥 वो सीन जो आपको पागल कर दें

👇 अभी 20 वीडियो फ्री में पाएं!
"""

VIDEO_SENT_TEXT = """
💦 *{} वीडियो आपके लिए तैयार हैं!* 💦

अगले 20 वीडियो पाने के लिए नीचे बटन दबाएं...
या नए सिरे से शुरू करें!

❤️ अगर आपको बॉट पसंद आया तो दोस्तों को भी बताएं!
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message"""
    user_id = update.effective_user.id
    if user_id in blocked_users:
        await update.message.reply_text("🚫 आपको ब्लॉक कर दिया गया है!")
        return
    
    username = update.effective_user.username or "No username"
    user_data[user_id] = {
        'verified': False, 
        'last_sent': 0, 
        'username': username, 
        'join_date': datetime.datetime.now(),
        'video_count': 0
    }
    
    # Notify admin
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"🆕 नया यूजर!\nID: {user_id}\nUsername: @{username}"
        )
    except Exception as e:
        logger.error(f"Error notifying admin: {e}")
    
    keyboard = [
        [InlineKeyboardButton("💋 चैनल ज्वाइन करें", url="https://t.me/your_channel")],
        [InlineKeyboardButton("🔥 वेरीफाई करें", callback_data='verify_join')]
    ]
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verify channel membership"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id in blocked_users:
        await query.edit_message_text("🚫 आपको ब्लॉक कर दिया गया है!")
        return
    
    try:
        member = await context.bot.get_chat_member(VERIFICATION_CHANNEL, query.from_user.id)
        if member.status in ['member', 'administrator', 'creator']:
            user_data[query.from_user.id]['verified'] = True
            await query.edit_message_text(
                VERIFIED_TEXT,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💦 20 वीडियो पाएं", callback_data='get_videos')]
                ]),
                parse_mode='Markdown'
            )
        else:
            await query.answer("❌ पहले चैनल ज्वाइन करें!", show_alert=True)
    except Exception as e:
        logger.error(f"Verification error: {e}")
        await query.answer("❌ वेरीफाई नहीं हो पाया. फिर से कोशिश करें.", show_alert=True)

async def send_videos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send video batch"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in blocked_users:
        await query.edit_message_text("🚫 आपको ब्लॉक कर दिया गया है!")
        return
    
    if not user_data.get(user_id, {}).get('verified'):
        await query.answer("पहले वेरीफाई करें!", show_alert=True)
        return
    
    await query.edit_message_text("💋 आपके वीडियो तैयार किए जा रहे हैं...")
    
    # Send 20 videos
    sent = 0
    last_msg = user_data[user_id]['last_sent']
    
    for msg_id in range(last_msg + 1, last_msg + 21):
        try:
            await context.bot.copy_message(
                chat_id=query.message.chat_id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id
            )
            sent += 1
            user_data[user_id]['video_count'] += 1
            time.sleep(1)  # Avoid flooding
        except Exception as e:
            logger.error(f"Error sending video {msg_id}: {e}")
    
    if sent > 0:
        user_data[user_id]['last_sent'] += sent
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=VIDEO_SENT_TEXT.format(sent),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💦 अगले 20 वीडियो", callback_data='next_batch')],
                [InlineKeyboardButton("🔥 नया सत्र", callback_data='get_videos')]
            ]),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text("❌ कोई वीडियो उपलब्ध नहीं है!")

# Admin commands
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot status"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ सिर्फ एडमिन के लिए!")
        return
    
    total_users = len(user_data)
    active_users = sum(1 for user in user_data.values() if user['verified'])
    total_videos = sum(user['video_count'] for user in user_data.values())
    
    status_text = f"""
📊 *बॉट स्टेटस* 📊

👥 कुल यूजर्स: {total_users}
💋 एक्टिव यूजर्स: {active_users}
🚫 ब्लॉक्ड यूजर्स: {len(blocked_users)}
🎬 भेजे गए वीडियो: {total_videos}
🆕 आज के नए यूजर्स: {sum(1 for user in user_data.values() if (datetime.datetime.now() - user['join_date']).days == 0)}
"""
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast message to all users"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ सिर्फ एडमिन के लिए!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast Your message")
        return
    
    message = ' '.join(context.args)
    success = 0
    failed = 0
    
    for user_id in user_data:
        try:
            await context.bot.send_message(user_id, f"📢 *एडमिन का संदेश:*\n\n{message}", parse_mode='Markdown')
            success += 1
        except Exception as e:
            logger.error(f"Error broadcasting to {user_id}: {e}")
            failed += 1
        time.sleep(0.5)  # Avoid rate limiting
    
    await update.message.reply_text(f"📣 ब्रॉडकास्ट रिजल्ट:\n✅ सफल: {success}\n❌ फेल: {failed}")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check server ping"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ सिर्फ एडमिन के लिए!")
        return
    
    start_time = time.time()
    message = await update.message.reply_text("🏓 पिंग चेक किया जा रहा है...")
    end_time = time.time()
    elapsed_time = round((end_time - start_time) * 1000, 2)
    
    await message.edit_text(f"⚡ सर्वर पिंग: {elapsed_time}ms")

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Block a user"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ सिर्फ एडमिन के लिए!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /block <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        blocked_users.add(user_id)
        await update.message.reply_text(f"✅ यूजर {user_id} को ब्लॉक कर दिया गया!")
    except ValueError:
        await update.message.reply_text("❌ गलत यूजर आईडी!")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unblock a user"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ सिर्फ एडमिन के लिए!")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /unblock <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        blocked_users.discard(user_id)
        await update.message.reply_text(f"✅ यूजर {user_id} को अनब्लॉक कर दिया!")
    except ValueError:
        await update.message.reply_text("❌ गलत यूजर आईडी!")

def main() -> None:
    """Run bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(verify_join, pattern="^verify_join$"))
    application.add_handler(CallbackQueryHandler(send_videos, pattern="^(get_videos|next_batch)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    
    # Admin handlers
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("block", block_user))
    application.add_handler(CommandHandler("unblock", unblock_user))
    
    # Start bot
    application.run_polling()
    logger.info("Bot is running...")

if __name__ == "__main__":
    main()
