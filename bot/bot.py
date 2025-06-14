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

# === Configuration ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_URL = os.environ.get("BACKEND_URL", "https://cryptominerbot-1.onrender.com")


# === Handlers ===

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


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username or "Miner"
    referral_code = context.args[0] if context.args else None
    try:
        response = requests.post(f"{API_URL}/register", json={
            "telegram_id": telegram_id,
            "username": username,
            "referral_code": referral_code
        })
        data = response.json()
        await update.message.reply_text(
            f"✅ {data.get('message')}\n🆔 ID: {telegram_id}\n🔗 Referral Code: {data.get('referral_code')}\n💰 Balance: {data.get('balance')}"
        )
    except Exception as e:
        print("❌ Register error:", e)
        await update.message.reply_text("⚠️ Registration failed. Try again.")


async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.post(f"{API_URL}/mine", params={"telegram_id": telegram_id})
        data = response.json()
        await update.message.reply_text(data.get("message"))
    except Exception as e:
        print("❌ Mine error:", e)
        await update.message.reply_text("⚠️ Mining failed. Try again later.")


async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.post(f"{API_URL}/spin", params={"telegram_id": telegram_id})
        data = response.json()
        await update.message.reply_text(data.get("message"))
    except Exception as e:
        print("❌ Spin error:", e)
        await update.message.reply_text("⚠️ Could not spin right now.")


async def quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.post(f"{API_URL}/quest", params={"telegram_id": telegram_id})
        data = response.json()
        await update.message.reply_text(data.get("message"))
    except Exception as e:
        print("❌ Quest error:", e)
        await update.message.reply_text("⚠️ Quest failed. Try again later.")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.get(f"{API_URL}/balance", params={"telegram_id": telegram_id})
        data = response.json()
        await update.message.reply_text(f"🏦 Balance: {data.get('balance', 0)} coins")
    except Exception as e:
        print("❌ Balance error:", e)
        await update.message.reply_text("⚠️ Could not fetch balance.")


async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.get(f"{API_URL}/balance", params={"telegram_id": telegram_id})
        data = response.json()
        code = data.get("referral_code")
        if code:
            bot_username = context.bot.username
            referral_link = f"https://t.me/{bot_username}?start={code}"
            await update.message.reply_text(f"📣 Invite your friends:\n🔗 {referral_link}")
        else:
            await update.message.reply_text("❌ No referral code available.")
    except Exception as e:
        print("❌ Refer error:", e)
        await update.message.reply_text("⚠️ Could not fetch referral code.")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🟢 Message: {update.message.text}")


# === Entrypoint ===
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

    print("✅ Telegram bot is running...")
    app.run_polling()
