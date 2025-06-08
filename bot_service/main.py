import logging
import os
import random
import threading
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, validator
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI App ===
app = FastAPI()

# === DB Setup ===
engine = create_engine("sqlite:///users.db", echo=True)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    telegram_id = Column(String, primary_key=True)
    balance = Column(Integer, default=0)
    wallet_address = Column(String, nullable=True)

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

# === Telegram Bot Setup ===
token = os.getenv("TELEGRAM_TOKEN")
telegram_app = None

if token:
    try:
        telegram_app = Application.builder().token(token).build()
        logger.info("Telegram bot initialized successfully")
    except Exception as e:
        logger.error(f"Telegram bot init error: {e}")
else:
    logger.error("❌ TELEGRAM_TOKEN not set")

# === Telegram Command Handlers ===
async def start(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            user = User(telegram_id=user_id, balance=0)
            db.add(user)
            db.commit()
            logger.info(f"New user registered: {user_id}")
        keyboard = [[InlineKeyboardButton("Open Mining Dashboard", web_app={"url": "https://crypto-miner-bot-web.onrender.com/miniapp"})]]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Welcome to CryptoMinerBot! Open your mining dashboard below:", reply_markup=markup)
    except Exception as e:
        logger.exception("Error in /start")
        await update.message.reply_text("An error occurred. Try again later.")
    finally:
        db.close()

async def register(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        existing = db.query(User).filter_by(telegram_id=user_id).first()
        if not existing:
            user = User(telegram_id=user_id, balance=0)
            db.add(user)
            db.commit()
            await update.message.reply_text(f"✅ Registered!\nID: {user_id}\nBalance: 0 coins.")
        else:
            await update.message.reply_text("ℹ️ You're already registered.")
    except Exception as e:
        logger.exception("Telegram /register error")
        await update.message.reply_text("⚠️ Could not register.")
    finally:
        db.close()

async def mine(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("Use /start first.")
            return
        user.balance += 10
        db.commit()
        await update.message.reply_text(f"✅ You mined 10 coins!\nNew balance: {user.balance}")
    except Exception as e:
        logger.exception("Mine error")
        await update.message.reply_text("An error occurred.")
    finally:
        db.close()

async def balance(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("Use /start first.")
            return
        await update.message.reply_text(f"💰 Your balance: {user.balance}")
    except Exception as e:
        logger.exception("Balance error")
        await update.message.reply_text("Could not fetch balance.")
    finally:
        db.close()

async def spin(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("Use /start first.")
            return
        win = random.randint(1, 10)
        user.balance += win
        db.commit()
        await update.message.reply_text(f"🎰 Spin result: {win}\nNew balance: {user.balance}")
    except Exception as e:
        logger.exception("Spin error")
        await update.message.reply_text("Could not spin.")
    finally:
        db.close()

async def quest(update, context):
    user_id = str(update.message.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("Use /start first.")
            return
        reward = random.randint(5, 15)
        user.balance += reward
        db.commit()
        await update.message.reply_text(f"🎯 Quest complete!\nEarned: {reward}\nBalance: {user.balance}")
    except Exception as e:
        logger.exception("Quest error")
        await update.message.reply_text("Error during quest.")
    finally:
        db.close()

# === API Models ===
class WalletLinkRequest(BaseModel):
    telegram_id: str
    wallet_address: str

    @validator("telegram_id", "wallet_address")
    def not_empty(cls, v):
        if not v.strip():
            raise ValueError("Must not be empty")
        return v

# === API Routes ===
@app.get("/")
@app.head("/")
def health():
    return {"message": "CryptoMinerBot is running"}

@app.get("/api/user/{telegram_id}")
def get_user(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"balance": user.balance, "wallet_address": user.wallet_address}
    finally:
        db.close()

@app.get("/api/mine/{telegram_id}")
def api_mine(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.balance += 10
        db.commit()
        return {"balance": user.balance}
    finally:
        db.close()

@app.post("/register")
def register_user(data: WalletLinkRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=data.telegram_id).first()
        if not user:
            user = User(telegram_id=data.telegram_id, balance=0)
            db.add(user)
            db.commit()
            return {"message": "✅ User registered", "telegram_id": data.telegram_id, "balance": user.balance}
        else:
            return {"message": "ℹ️ User already registered", "telegram_id": user.telegram_id, "balance": user.balance}
    except Exception as e:
        logger.exception("Register error")
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
        return {"message": "✅ Wallet linked successfully", "wallet_address": user.wallet_address}
    except Exception as e:
        logger.exception("Link wallet error")
        raise HTTPException(status_code=500, detail="Internal error")
    finally:
        db.close()

@app.post("/api/register")
def register_user_q(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, balance=0)
            db.add(user)
            db.commit()
            return {"message": "✅ User registered", "telegram_id": telegram_id, "balance": user.balance}
        else:
            return {"message": "ℹ️ User already registered", "telegram_id": user.telegram_id, "balance": user.balance}
    except Exception as e:
        logger.exception("Query-based register error")
        raise HTTPException(status_code=500, detail="Registration failed")
    finally:
        db.close()

@app.post("/api/link-wallet")
def link_wallet_q(telegram_id: str, wallet_address: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.wallet_address = wallet_address
        db.commit()
        return {"message": "✅ Wallet linked", "wallet_address": wallet_address}
    except Exception as e:
        logger.exception("Query-based link wallet error")
        raise HTTPException(status_code=500, detail="Wallet link failed")
    finally:
        db.close()

@app.get("/miniapp")
def miniapp():
    return HTMLResponse("<h1>✅ CryptoMinerBot MiniApp Connected</h1>")

# === Run Telegram Bot ===
if telegram_app:
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("register", register))
    telegram_app.add_handler(CommandHandler("mine", mine))
    telegram_app.add_handler(CommandHandler("balance", balance))
    telegram_app.add_handler(CommandHandler("spin", spin))
    telegram_app.add_handler(CommandHandler("quest", quest))

    def run_bot():
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        telegram_app.run_polling()

    threading.Thread(target=run_bot, daemon=True).start()
else:
    logger.warning("Telegram bot not started.")

# === Run Server ===
if __name__ == "__main__":
    logger.info("Starting server on http://0.0.0.0:10000")
    uvicorn.run(app, host="0.0.0.0", port=10000)
