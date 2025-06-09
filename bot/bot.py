# bot.py
import os, logging, random, datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === DB Setup ===
Base = declarative_base()
engine = create_engine("sqlite:///users.db", echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
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

# === Telegram Commands ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "User"
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            code = f"{user_id[-6:]}_{random.randint(1000,9999)}"
            user = User(telegram_id=user_id, username=username, balance=0, referral_code=code)
            db.add(user)
            db.commit()
        keyboard = [[InlineKeyboardButton("💼 Open Dashboard", web_app={"url": "https://cryptominer-ui-two.vercel.app"})]]
        await update.message.reply_text("👋 Welcome to CryptoMiner!", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        db.close()

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "User"
    referred_by = context.args[0] if context.args else None
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            code = f"{user_id[-6:]}_{random.randint(1000,9999)}"
            user = User(telegram_id=user_id, username=username, balance=0, referral_code=code, referred_by=referred_by)
            db.add(user)
            db.commit()
            await update.message.reply_text(f"✅ Registered!\nReferral code: {code}")
        else:
            await update.message.reply_text("ℹ️ You're already registered.")
    finally:
        db.close()

async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ Use /register first.")
            return
        now = datetime.datetime.utcnow()
        if user.last_mined and (now - user.last_mined).total_seconds() < 60:
            await update.message.reply_text("⏳ Cooldown: Wait 60s between mining.")
            return
        reward = random.randint(1, 10)
        user.balance += reward
        user.last_mined = now
        db.commit()
        await update.message.reply_text(f"⛏️ You mined {reward} coins!\n💰 Balance: {user.balance:.2f}")
    finally:
        db.close()

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ Use /register first.")
            return
        now = datetime.datetime.utcnow()
        if user.last_spun and (now - user.last_spun).total_seconds() < 60:
            await update.message.reply_text("⏳ Cooldown: Wait 60s between spins.")
            return
        reward = random.randint(0, 15)
        user.balance += reward
        user.last_spun = now
        user.last_spin_reward = reward
        db.commit()
        await update.message.reply_text(f"🎰 You spun and won {reward} coins!\n💰 Balance: {user.balance:.2f}")
    finally:
        db.close()

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if user:
            await update.message.reply_text(f"💰 Your balance: {user.balance:.2f}")
        else:
            await update.message.reply_text("❌ Use /register first.")
    finally:
        db.close()

# === Bot Launch ===
if __name__ == "__main__":
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN not set in environment variables")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("mine", mine))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(CommandHandler("balance", balance))

    print("✅ Telegram bot started.")
    app.run_polling()
