import logging
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "8180063318:AAG2FtpVESnPYKuEszDIaewy-LXgVXXDS-o"
CHANNEL_ID = -1002441094491  # Private channel ID (with -100 prefix)
ADMIN_USER_IDS = [8167507955]  # Your user ID(s) who can control the bot

# List of video message IDs from the channel
VIDEO_MESSAGE_IDS = [8915, 8916, 8917]  # Example message IDs from your channel

async def is_admin(update: Update) -> bool:
    """Check if user is admin."""
    return update.effective_user.id in ADMIN_USER_IDS

async def post_init(application: Application) -> None:
    """Post initialization - set bot commands."""
    await application.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("sendvideos", "Send all videos from private channel"),
        BotCommand("sendvideo", "Send specific video (usage: /sendvideo [id])")
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message."""
    if not await is_admin(update):
        await update.message.reply_text("⚠️ You are not authorized to use this bot.")
        return
    
    commands = [
        "/start - Show this message",
        "/sendvideos - Send all videos from private channel",
        "/sendvideo [id] - Send specific video by message ID",
        "",
        f"Channel ID: {CHANNEL_ID}",
        "Example private link: https://t.me/c/2441094491/8915"
    ]
    
    await update.message.reply_text("\n".join(commands))

async def send_videos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send all videos from the channel."""
    if not await is_admin(update):
        await update.message.reply_text("⚠️ You are not authorized to use this command.")
        return
    
    chat_id = update.effective_chat.id
    bot = context.bot
    
    await update.message.reply_text(f"⏳ Preparing to send {len(VIDEO_MESSAGE_IDS)} videos...")
    
    success_count = 0
    for msg_id in VIDEO_MESSAGE_IDS:
        try:
            # Copy the message instead of forwarding to preserve original sender
            await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id
            )
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send video {msg_id}: {e}")
            await update.message.reply_text(f"❌ Failed to send video ID {msg_id}")
    
    await update.message.reply_text(f"✅ Done! Successfully sent {success_count}/{len(VIDEO_MESSAGE_IDS)} videos")

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send specific video by message ID."""
    if not await is_admin(update):
        await update.message.reply_text("⚠️ You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /sendvideo [message_id]\nExample: /sendvideo 8915")
        return
    
    try:
        msg_id = int(context.args[0])
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=CHANNEL_ID,
            message_id=msg_id
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid message ID. Please provide a number.")
    except Exception as e:
        logger.error(f"Failed to send video {msg_id}: {e}")
        await update.message.reply_text(f"❌ Failed to send video ID {msg_id}")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("sendvideos", send_videos))
    application.add_handler(CommandHandler("sendvideo", send_video))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
