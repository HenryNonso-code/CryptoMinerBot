import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# === Configuration ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Read token securely from env
API_URL = "https://cryptominerbot-1.onrender.com"

# === Bot Commands ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    message = (
        f"👋 Welcome {name}!\n\n"
        "Use the commands below:\n"
        "/register - Create your account (optionally with a referral code)\n"
        "/mine - Start mining ⛏️\n"
        "/spin - Try your luck 🎰\n"
        "/quest - Complete a quest 🎯\n"
        "/balance - Check your wallet 💰\n"
        "/refer - Invite friends 👥 and earn rewards!"
    )
    await update.message.reply_text(message)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    referral_code = context.args[0] if context.args else None

    try:
        response = requests.post(
            f"{API_URL}/register",
            json={"telegram_id": telegram_id, "referral_code": referral_code}
        )
        data = response.json()
        msg = (
            f"✅ Registered!\n"
            f"🆔 ID: {data['id']}\n"
            f"🔗 Referral Code: {data['referral_code']}\n"
            f"💰 Balance: {data['balance']} coins\n"
            f"{data.get('message', '')}"
        )
        await update.message.reply_text(msg)
    except Exception as e:
        print("❌ Register error:", e)
        await update.message.reply_text("⚠️ Registration failed. Try again.")

async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.post(f"{API_URL}/mine", params={"telegram_id": telegram_id})
        data = response.json()
        msg = data.get("message") or f"⛏️ You mined {data.get('amount')} coins!\nNew balance: {data.get('balance')}"
        await update.message.reply_text(msg)
    except Exception as e:
        print("❌ Mine error:", e)
        await update.message.reply_text("⚠️ Mining failed. Try again later.")

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.post(f"{API_URL}/spin", params={"telegram_id": telegram_id})
        data = response.json()
        msg = f"🎰 Spin result: {data.get('amount')} coins\n💰 New balance: {data.get('balance')}"
        await update.message.reply_text(msg)
    except Exception as e:
        print("❌ Spin error:", e)
        await update.message.reply_text("⚠️ Could not spin right now.")

async def quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.post(f"{API_URL}/quest", params={"telegram_id": telegram_id})
        data = response.json()
        msg = f"🎯 Quest complete!\n🏆 Earned: {data.get('amount')} coins\n💰 New balance: {data.get('balance')}"
        await update.message.reply_text(msg)
    except Exception as e:
        print("❌ Quest error:", e)
        await update.message.reply_text("⚠️ Quest failed. Try again later.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.get(f"{API_URL}/balance", params={"telegram_id": telegram_id})
        data = response.json()
        msg = f"🏦 Your balance: {data.get('balance')} coins"
        await update.message.reply_text(msg)
    except Exception as e:
        print("❌ Balance error:", e)
        await update.message.reply_text("⚠️ Could not fetch balance.")

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    try:
        response = requests.get(f"{API_URL}/balance", params={"telegram_id": telegram_id})
        data = response.json()
        code = data.get("referral_code")
        referrals = data.get("referrals", 0)
        if code:
            bot_username = context.bot.username
            link = f"https://t.me/{bot_username}?start={code}"
            msg = f"📣 Invite others to join:\n🔗 {link}\n👥 Referrals: {referrals}"
        else:
            msg = "⚠️ Referral code not available. Try registering again."
        await update.message.reply_text(msg)
    except Exception as e:
        print("❌ Refer error:", e)
        await update.message.reply_text("⚠️ Could not fetch referral info.")

# === Debug echo ===
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"🟢 Received message: {update.message.text}")

# === Main Entrypoint ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("mine", mine))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(CommandHandler("quest", quest))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("refer", refer))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

    print("✅ Telegram bot is running...")
    app.run_polling()
