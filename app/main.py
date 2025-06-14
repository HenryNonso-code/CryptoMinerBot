import os, logging, random, datetime, asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI App ===
app = FastAPI()

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cryptominer-2fropgxp9-johec-teams-projects.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# === Telegram Setup ===
token = os.getenv("TELEGRAM_TOKEN")
telegram_app = Application.builder().token(token).build() if token else None

# === Telegram Handlers ===
async def start(update, context):
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or "User"
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            referral = f"{user_id[-6:]}_{random.randint(1000,9999)}"
            user = User(telegram_id=user_id, username=username, balance=0, referral_code=referral)
            db.add(user)
            db.commit()

        keyboard = [[
            InlineKeyboardButton("💼 Open Dashboard", web_app=WebAppInfo(url="https://cryptominer-2fropgxp9-johec-teams-projects.vercel.app"))
        ]]

        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("👋 Welcome to CryptoMiner!", reply_markup=markup)
    except Exception as e:
        logger.exception("Start error")
        await update.message.reply_text("⚠️ Something went wrong.")
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
            user = User(telegram_id=user_id, username=username, balance=0, referral_code=referral_code, referred_by=referral_by)
            db.add(user)
            db.commit()
            await update.message.reply_text(f"✅ Registered!\nReferral code: {referral_code}")
        else:
            await update.message.reply_text("ℹ️ You're already registered.")
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
        await update.message.reply_text(f"⛏️ You mined {reward} coins.\n💰 Balance: {user.balance:.2f}")
    finally:
        db.close()

async def spin(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("❌ Please /register first.")
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

# === FastAPI Models and Routes ===
class RegisterRequest(BaseModel):
    telegram_id: str
    username: str = "User"
    referral_code: str | None = None

@app.post("/register")
def api_register(req: RegisterRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=req.telegram_id).first()
        if user:
            return {"message": "Already registered", "balance": user.balance, "referral_code": user.referral_code}
        new_code = f"{req.telegram_id[-6:]}_{random.randint(1000,9999)}"
        user = User(
            telegram_id=req.telegram_id,
            username=req.username,
            referral_code=new_code,
            referred_by=req.referral_code
        )
        db.add(user)
        db.commit()
        return {"message": "Registered", "id": user.id, "balance": user.balance, "referral_code": new_code}
    finally:
        db.close()

@app.post("/mine")
def api_mine(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Not registered")
        now = datetime.datetime.utcnow()
        if user.last_mined and (now - user.last_mined).total_seconds() < 60:
            return {"message": "Cooldown active"}
        coins = random.randint(1, 10)
        user.balance += coins
        user.last_mined = now
        db.commit()
        return {"message": f"Mined {coins} coins", "coins": coins, "balance": user.balance}
    finally:
        db.close()

@app.post("/spin")
def api_spin(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Not registered")
        now = datetime.datetime.utcnow()
        if user.last_spun and (now - user.last_spun).total_seconds() < 60:
            return {"message": "Cooldown active"}
        coins = random.randint(0, 15)
        user.balance += coins
        user.last_spun = now
        user.last_spin_reward = coins
        db.commit()
        return {"message": f"Spun and won {coins} coins", "amount": coins, "balance": user.balance}
    finally:
        db.close()

@app.post("/quest")
def api_quest(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Not registered")
        reward = random.randint(2, 12)
        user.balance += reward
        user.quests_completed = (user.quests_completed or "") + f",Q{random.randint(1,100)}"
        db.commit()
        return {"message": "Quest complete", "amount": reward, "balance": user.balance}
    finally:
        db.close()

@app.get("/balance")
def api_balance(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Not registered")
        return {
            "balance": user.balance,
            "referral_code": user.referral_code,
            "referrals": 0
        }
    finally:
        db.close()

@app.get("/leaderboard")
def api_leaderboard(limit: int = 10):
    db = SessionLocal()
    try:
        users = (
            db.query(User)
            .order_by(User.balance.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "username": user.username,
                "telegram_id": user.telegram_id,
                "balance": round(user.balance, 2)
            }
            for user in users
        ]
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "✅ CryptoMiner API working"}

# === Launch ===
if __name__ == "__main__":
    import threading
    def run_bot():
        telegram_app.add_handler(CommandHandler("start", start))
        telegram_app.add_handler(CommandHandler("register", register))
        telegram_app.add_handler(CommandHandler("mine", mine))
        telegram_app.add_handler(CommandHandler("spin", spin))
        telegram_app.add_handler(CommandHandler("balance", balance))
        telegram_app.run_polling()

    if telegram_app:
        threading.Thread(target=run_bot, daemon=True).start()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
