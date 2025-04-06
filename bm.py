import os
import random
import asyncio
from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "7910030892:AAF87kCl5kBESWxPfaMSUJS0himIaBj2nCI"  # REPLACE THIS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message"""
    await update.message.reply_text("🌟 Welcome to Proxy Bot! Use /gen_proxy or /help")

async def gen_proxy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate proxies command"""
    await update.message.reply_text("How many proxies? (Max 100)")

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the number input"""
    try:
        if update.message.reply_to_message and "How many proxies" in update.message.reply_to_message.text:
            num = min(int(update.message.text), 100)
            proxies = [f"proxy_{i}.com:8080" for i in range(num)]
            
            # Save to temp file
            filename = "proxies.txt"
            with open(filename, "w") as f:
                f.write("\n".join(proxies))
            
            # Send file
            with open(filename, "rb") as f:
                await update.message.reply_document(
                    document=InputFile(f),
                    caption=f"Here are your {num} proxies!"
                )
            
            # Clean up
            os.remove(filename)
    except ValueError:
        await update.message.reply_text("Please send a valid number!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command"""
    await update.message.reply_text("/start - Welcome\n/gen_proxy - Generate proxies\n/help - This message")

def main() -> None:
    """Start the bot"""
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen_proxy", gen_proxy))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
