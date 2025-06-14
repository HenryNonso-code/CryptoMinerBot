import os
import requests
from telegram import Update, KeyboardButton, WebAppInfo, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_URL = os.environ.get("BACKEND_URL", "https://cryptominerbot-1.onrender.com")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "Miner"
    keyboard = [
        [KeyboardButton("🚀 Open JOHEC App", web_app=WebAppInfo(url="https://cryptominer-ui-two.vercel.app"))]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    msg = (
        f"👋 Hello {name}!\n\n"
        "Welcome to JOHEC CryptoMinerBot.\n\n"
        "💡 Use these commands:\n"
        "/register - Register an account (use a referral code if you have one)\n"
        "/mine - Mine coins ⛏️\n"
        "/spin - Spin the wheel 🎰\n"
        "/quest - Complete a quest 🎯\n"
        "/balance - Check your balance 💰\n"
        "/refer - Get your referral link 👥\n\n"
        "👇 Or tap below to access the dashboard."
    )
    await update.message.reply_text(msg, reply_markup=reply_markup)

# Other handlers remain the same...
# (register, mine, spin, quest, balance, refer)

# Entrypoint
if __name__ == "__main__":
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN environment variable is missing")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("mine", mine))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(CommandHandler("quest", quest))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("refer", refer))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("✅ Telegram bot is running...")  # 🔥 This must show up in Render logs
    app.run_polling()
