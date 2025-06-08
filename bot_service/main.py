# main.py
import os, logging, random, threading
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel, validator
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI App ===
app = FastAPI()

# === DB Setup ===
Base = declarative_base()
engine = create_engine("sqlite:///users.db", echo=True)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    telegram_id = Column(String, primary_key=True)
    balance = Column(Integer, default=0)
    wallet_address = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# === Telegram Setup ===
token = os.getenv("TELEGRAM_TOKEN")
telegram_app = None

if token:
    telegram_app = Application.builder().token(token).build()
    logger.info("✅ Telegram bot initialized")
else:
    logger.warning("❌ TELEGRAM_TOKEN not set")

# === Command Handlers ===
async def start(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            user = User(telegram_id=user_id, balance=0)
            db.add(user)
            db.commit()
        keyboard = [[InlineKeyboardButton("🧱 Open MiniApp", web_app={"url": "https://cryptominer-ui-two.vercel.app"})]]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("👋 Welcome Henry!\n\nUse the buttons below to open your dashboard.", reply_markup=markup)
    except Exception as e:
        logger.exception("Start error")
        await update.message.reply_text("⚠️ Failed to initialize.")
    finally:
        db.close()

async def register(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        if not db.query(User).filter_by(telegram_id=user_id).first():
            db.add(User(telegram_id=user_id, balance=0))
            db.commit()
            await update.message.reply_text("✅ Registration complete!")
        else:
            await update.message.reply_text("ℹ️ You're already registered.")
    except Exception:
        logger.exception("Register error")
        await update.message.reply_text("⚠️ Registration failed. Try again.")
    finally:
        db.close()

async def mine(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("⚠️ You need to /register first.")
            return
        coins = random.randint(1, 10)
        user.balance += coins
        db.commit()
        await update.message.reply_text(f"⛏ You mined {coins} coins!\n💰 New balance: {user.balance}")
    except Exception:
        logger.exception("Mine error")
        await update.message.reply_text("⚠️ Failed to mine.")
    finally:
        db.close()

async def spin(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("⚠️ You need to /register first.")
            return
        result = random.randint(1, 8)
        user.balance += result
        db.commit()
        await update.message.reply_text(f"🎰 Spin result: {result} coins\n💰 New balance: {user.balance}")
    except Exception:
        logger.exception("Spin error")
        await update.message.reply_text("⚠️ Spin failed.")
    finally:
        db.close()

async def balance(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("⚠️ You need to /register first.")
            return
        await update.message.reply_text(f"💰 Balance: {user.balance} coins")
    except Exception:
        logger.exception("Balance error")
        await update.message.reply_text("⚠️ Failed to fetch balance.")
    finally:
        db.close()

# === FastAPI Models & Routes ===
class WalletLinkRequest(BaseModel):
    telegram_id: str
    wallet_address: str

    @validator("telegram_id", "wallet_address")
    def validate(cls, v):
        if not v.strip():
            raise ValueError("Field must not be empty")
        return v

@app.get("/")
def root():
    return {"message": "✅ CryptoMinerBot backend is running"}

@app.post("/register")
def register_user(data: WalletLinkRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=data.telegram_id).first()
        if not user:
            user = User(telegram_id=data.telegram_id, balance=0)
            db.add(user)
            db.commit()
            return {"message": "✅ User registered", "balance": 0}
        return {"message": "ℹ️ Already registered", "balance": user.balance}
    except Exception:
        logger.exception("API /register error")
        raise HTTPException(status_code=500, detail="Registration failed")
    finally:
        db.close()

@app.post("/link-wallet")
def link_wallet(data: WalletLinkRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=data.telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.wallet_address = data.wallet_address
        db.commit()
        return {"message": "✅ Wallet linked", "wallet_address": data.wallet_address}
    except Exception:
        logger.exception("API /link-wallet error")
        raise HTTPException(status_code=500, detail="Link failed")
    finally:
        db.close()

@app.get("/miniapp")
def miniapp():
    return HTMLResponse("<h3>✅ MiniApp is connected</h3>")

# === Run Telegram Bot ===
if telegram_app:
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("register", register))
    telegram_app.add_handler(CommandHandler("mine", mine))
    telegram_app.add_handler(CommandHandler("spin", spin))
    telegram_app.add_handler(CommandHandler("balance", balance))

    def run_bot():
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        telegram_app.run_polling()

    threading.Thread(target=run_bot, daemon=True).start()

# === Run FastAPI ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
