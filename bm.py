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
import asyncio

# Bot Configuration - UPDATE THESE WITH YOUR ACTUAL VALUES
BOT_TOKEN = "8125880528:AAHRUQpcmN645oKmvjt8OeGSGVjG_9Aas38"
CHANNEL_ID = -1001234567890  # Replace with your actual channel ID with videos
VERIFICATION_CHANNEL = -1001234567891  # Replace with your actual channel ID users must join
ADMIN_ID = 8167507955  # Your admin ID
START_IMAGE_URL = "https://t.me/botstomp/125"  # Image for start and next buttons

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

⚠️ नोट: वीडियो 1 मिनट बाद अपने आप डिलीट हो जाएंगे!
"""

application = None  # Global application variable

async def delete_message(chat_id, message_id):
    """Delete a specific message"""
    try:
        await application.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Deleted message {message_id} in chat {chat_id}")
    except Exception as e:
        logger.error(f"Error deleting message {message_id}: {e}")

async def delete_after_delay(chat_id, message_id, delay=60):
    """Delete message after specified delay"""
    await asyncio.sleep(delay)
    await delete_message(chat_id, message_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with image"""
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
        'video_count': 0,
        'last_verify_attempt': 0
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
        [InlineKeyboardButton("💋 चैनल ज्वाइन करें", url="https://t.me/+LNs_qcLHlbNkN2E1")],
        [InlineKeyboardButton("🔥 वेरीफाई करें", callback_data='verify_join')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send image with caption
    try:
        sent_message = await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=START_IMAGE_URL,
            caption=WELCOME_TEXT,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error sending image: {e}")
        sent_message = await update.message.reply_text(
            WELCOME_TEXT,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    # Schedule welcome message deletion after 5 minutes
    asyncio.create_task(delete_after_delay(update.effective_chat.id, sent_message.message_id, 300))

async def verify_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verify channel membership with improved error handling"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in blocked_users:
        await query.edit_message_text("🚫 आपको ब्लॉक कर दिया गया है!")
        return
    
    # Check verification cooldown
    if time.time() - user_data[user_id].get('last_verify_attempt', 0) < 10:
        await query.answer("❌ बहुत जल्दी! 10 सेकंड बाद कोशिश करें", show_alert=True)
        return
    
    user_data[user_id]['last_verify_attempt'] = time.time()
    
    try:
        # Check if user is member of verification channel
        member = await context.bot.get_chat_member(VERIFICATION_CHANNEL, user_id)
        logger.info(f"Verification attempt by user {user_id} - Status: {member.status}")
        
        if member.status in ['member', 'administrator', 'creator']:
            user_data[user_id]['verified'] = True
            
            # Create keyboard for next step
            keyboard = [
                [InlineKeyboardButton("💦 20 वीडियो पाएं", callback_data='get_videos')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                # Try to send new message with image
                await query.message.delete()
                sent_message = await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=START_IMAGE_URL,
                    caption=VERIFIED_TEXT,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Error sending image: {e}")
                # Fallback to text message
                sent_message = await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=VERIFIED_TEXT,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            
            # Schedule deletion
            asyncio.create_task(delete_after_delay(query.message.chat_id, sent_message.message_id, 300))
            
        else:
            # User hasn't joined the channel
            await query.answer(
                "❌ पहले चैनल ज्वाइन करें फिर वेरीफाई बटन दबाएं!", 
                show_alert=True
            )
            
            # Show join button again
            keyboard = [
                [InlineKeyboardButton("💋 चैनल ज्वाइन करें", url="https://t.me/+LNs_qcLHlbNkN2E1")],
                [InlineKeyboardButton("🔥 वेरीफाई करें", callback_data='verify_join')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_reply_markup(reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Verification error for user {user_id}: {e}")
        await query.answer(
            "❌ वेरीफाई नहीं हो पाया. बाद में कोशिश करें.", 
            show_alert=True
        )

async def send_videos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send video batch with auto-delete after 60 seconds"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id in blocked_users:
        await query.edit_message_text("🚫 आपको ब्लॉक कर दिया गया है!")
        return
    
    if not user_data.get(user_id, {}).get('verified'):
        await query.answer("पहले वेरीफाई करें!", show_alert=True)
        return
    
    # Edit the current message to show processing status
    processing_msg = await query.edit_message_text("💋 आपके वीडियो तैयार किए जा रहे हैं...")
    
    # Send 20 videos with auto-delete
    sent = 0
    last_msg = user_data[user_id]['last_sent']
    chat_id = query.message.chat_id
    
    # List to store all sent message IDs
    sent_message_ids = []
    
    for msg_id in range(last_msg + 1, last_msg + 21):
        try:
            sent_message = await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id
            )
            sent += 1
            user_data[user_id]['video_count'] += 1
            sent_message_ids.append(sent_message.message_id)
            
            # Add small delay between sends to avoid flooding
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Error sending video {msg_id}: {e}")
    
    # Delete the processing message
    await delete_message(chat_id, processing_msg.message_id)
    
    if sent > 0:
        user_data[user_id]['last_sent'] += sent
        
        # Create keyboard for next actions
        keyboard = [
            [InlineKeyboardButton("💦 अगले 20 वीडियो", callback_data='next_batch')],
            [InlineKeyboardButton("🔥 नया सत्र", callback_data='get_videos')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send status message with image
        try:
            status_message = await context.bot.send_photo(
                chat_id=chat_id,
                photo=START_IMAGE_URL,
                caption=VIDEO_SENT_TEXT.format(sent),
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error sending image: {e}")
            status_message = await context.bot.send_message(
                chat_id=chat_id,
                text=VIDEO_SENT_TEXT.format(sent),
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        # Schedule deletion of all sent messages (videos and status) after 60 seconds
        for msg_id in sent_message_ids:
            asyncio.create_task(delete_after_delay(chat_id, msg_id))
        asyncio.create_task(delete_after_delay(chat_id, status_message.message_id))
    else:
        error_message = await context.bot.send_message(
            chat_id=chat_id,
            text="❌ कोई वीडियो उपलब्ध नहीं है!"
        )
        asyncio.create_task(delete_after_delay(chat_id, error_message.message_id))

# ... [Keep all your other existing functions unchanged] ...

def main() -> None:
    """Run bot"""
    global application
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
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("sendvideo", send_custom_video))
    
    # Start bot
    application.run_polling()
    logger.info("Bot is running...")

if __name__ == "__main__":
    main()
