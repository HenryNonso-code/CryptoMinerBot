import os, logging, random, datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === DB Setup ===
Base = declarative_base()
engine = create_engine("sqlite:///users.db", echo=False, connect_args={"check_same_thread": False})
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

# === Bot Token ===
token = os.getenv("TELEGRAM_TOKEN")
telegram_app = Application.builder().token(token).build() if token else None

# === Handlers ===
async def start(update, context):
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "User"
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            referral = f"{user_id[-6:]}_{random.randint(1000, 9999)}"
            user = User(telegram_id=user_id, username=username, referral_code=referral)
            db.add(user)
            db.commit()
        keyboard = [[InlineKeyboardButton("💼 Open Dashboard", web_app={"url": "https://cryptominer-2c5dkmlie-johec-teams-projects.vercel.app"})]]

        await update.message.reply_text("👋 Welcome to CryptoMiner!", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        db.close()

async def register(update, context):
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "User"
    referral_by = context.args[0] if context.args else None
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            referral_code = f"{user_id[-6:]}_{random.randint(1000,9999)}"
            user = User(telegram_id=user_id, username=username, referral_code=referral_code, referred_by=referral_by)
            db.add(user)
            db.commit()
            await update.message.reply_text(f"✅ Registered!\nReferral code: {referral_code}")
        else:
            await update.message.reply_text("ℹ You're already registered.")
    finally:
        db.close()

async def mine(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ You must /register first.")
            return
        now = datetime.datetime.utcnow()
        if user.last_mined and (now - user.last_mined).total_seconds() < 60:
            await update.message.reply_text("⏳ Cooldown: Wait 60 seconds between mining.")
            return
        reward = random.randint(1, 10)
        user.balance += reward
        user.last_mined = now
        db.commit()
        await update.message.reply_text(f"⛏ You mined {reward} coins.\n💰 Balance: {user.balance:.2f}")
    finally:
        db.close()

async def spin(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ You must /register first.")
            return
        now = datetime.datetime.utcnow()
        if user.last_spun and (now - user.last_spun).total_seconds() < 60:
            await update.message.reply_text("⏳ Cooldown: Wait 60 seconds between spins.")
            return
        reward = random.randint(0, 15)
        user.balance += reward
        user.last_spun = now
        user.last_spin_reward = reward
        db.commit()
        await update.message.reply_text(f"🎰 You spun and won {reward} coins!\n💰 Balance: {user.balance:.2f}")
    finally:
        db.close()

async def quest(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ You must /register first.")
            return
        reward = random.randint(2, 12)
        user.balance += reward
        user.quests_completed = (user.quests_completed or "") + f",Q{random.randint(1,100)}"
        db.commit()
        await update.message.reply_text(f"🎯 Quest complete! You earned {reward} coins.\n💰 Balance: {user.balance:.2f}")
    finally:
        db.close()

async def balance(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if user:
            await update.message.reply_text(f"💰 Your balance: {user.balance:.2f} coins")
        else:
            await update.message.reply_text("❌ You're not registered. Use /register.")
    finally:
        db.close()

# === Run Bot ===
def main():
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("register", register))
    telegram_app.add_handler(CommandHandler("mine", mine))
    telegram_app.add_handler(CommandHandler("spin", spin))
    telegram_app.add_handler(CommandHandler("quest", quest))
    telegram_app.add_handler(CommandHandler("balance", balance))
    telegram_app.run_polling()

if __name__ == "__main__":
    main()
