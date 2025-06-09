# main.py
import os, logging, random, datetime, asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI App ===
app = FastAPI()

# === DB Setup ===
Base = declarative_base()
engine = create_engine("sqlite:///users.db", echo=True, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True)
    username = Column(String)
    balance = Column(Float, default=0)
    referral_code = Column(String, unique=True)
    referred_by = Column(String)
    last_mined = Column(DateTime)
    last_spun = Column(DateTime)
    last_spin_reward = Column(Float, default=0)
    quests_completed = Column(String, default="")
    referral_points = Column(Integer, default=0)

Base.metadata.create_all(bind=engine)

# === Telegram Bot Setup ===
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

# === Telegram Command Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "User"
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            referral_code = f"{user_id[-6:]}_{random.randint(1000,9999)}"
            user = User(telegram_id=user_id, username=username, referral_code=referral_code)
            db.add(user)
            db.commit()
        keyboard = [[InlineKeyboardButton("💼 Open Dashboard", web_app={"url": "https://cryptominer-ui-two.vercel.app"})]]
        await update.message.reply_text("👋 Welcome to CryptoMiner!", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        db.close()

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "User"
    referral_by = context.args[0] if context.args else None
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            code = f"{user_id[-6:]}_{random.randint(1000,9999)}"
            new_user = User(telegram_id=user_id, username=username, referral_code=code, referred_by=referral_by)
            db.add(new_user)
            db.commit()
            await update.message.reply_text(f"✅ Registered!\nReferral code: {code}")
        else:
            await update.message.reply_text("ℹ️ You're already registered.")
    finally:
        db.close()

async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ Please /register first.")
            return
        now = datetime.datetime.utcnow()
        if user.last_mined and (now - user.last_mined).total_seconds() < 60:
            await update.message.reply_text("⏳ Cooldown active. Try again in 60 seconds.")
            return
        reward = random.randint(1, 10)
        user.balance += reward
        user.last_mined = now
        db.commit()
        await update.message.reply_text(f"⛏️ You mined {reward} coins.\n💰 Balance: {user.balance:.2f}")
    finally:
        db.close()

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ Please /register first.")
            return
        now = datetime.datetime.utcnow()
        if user.last_spun and (now - user.last_spun).total_seconds() < 60:
            await update.message.reply_text("⏳ Cooldown active. Try again in 60 seconds.")
            return
        reward = random.randint(1, 15)
        user.balance += reward
        user.last_spun = now
        user.last_spin_reward = reward
        db.commit()
        await update.message.reply_text(f"🎰 You won {reward} coins!\n💰 Balance: {user.balance:.2f}")
    finally:
        db.close()

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if user:
            await update.message.reply_text(f"💰 Balance: {user.balance:.2f} coins")
        else:
            await update.message.reply_text("❌ You're not registered. Use /register")
    finally:
        db.close()

async def quest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ Please /register first.")
            return
        reward = random.randint(2, 12)
        user.balance += reward
        user.quests_completed = (user.quests_completed or "") + f",Q{random.randint(1,100)}"
        db.commit()
        await update.message.reply_text(f"🎯 Quest done!\n🏆 Earned: {reward} coins\n💰 New balance: {user.balance:.2f}")
    finally:
        db.close()

# === FastAPI endpoint
@app.get("/")
def health():
    return {"message": "✅ CryptoMinerBot API active"}

# === Run Uvicorn & Telegram App ===
async def main():
    from uvicorn import Config, Server
    config = Config(app=app, host="0.0.0.0", port=10000)
    server = Server(config)

    tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CommandHandler("register", register))
    tg_app.add_handler(CommandHandler("mine", mine))
    tg_app.add_handler(CommandHandler("spin", spin))
    tg_app.add_handler(CommandHandler("balance", balance))
    tg_app.add_handler(CommandHandler("quest", quest))

    await asyncio.gather(
        server.serve(),
        tg_app.run_polling()
    )

if __name__ == "__main__":
    asyncio.run(main())
