# === FINAL FIXED main.py ===

import os
import logging
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

# === FastAPI ===
app = FastAPI()

# === Database Setup ===
engine = create_engine("sqlite:///users.db")
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    telegram_id = Column(String, primary_key=True)
    balance = Column(Integer, default=0)
    wallet_address = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# === Pydantic Models ===
class RegisterRequest(BaseModel):
    telegram_id: str
    wallet_address: str

    @validator("telegram_id", "wallet_address")
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field must not be empty")
        return v

# === API ENDPOINTS ===

@app.get("/")
def root():
    return {"message": "CryptoMinerBot API Running"}

@app.post("/register")
def register_user(data: RegisterRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=data.telegram_id).first()
        if not user:
            user = User(telegram_id=data.telegram_id, balance=0)
            db.add(user)
            db.commit()
            return {"message": "✅ User registered", "telegram_id": user.telegram_id, "balance": user.balance}
        return {"message": "ℹ️ User already registered", "telegram_id": user.telegram_id, "balance": user.balance}
    except Exception as e:
        logger.exception("Register failed")
        raise HTTPException(status_code=500, detail="Registration failed")
    finally:
        db.close()

@app.post("/link-wallet")
def link_wallet(data: RegisterRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=data.telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.wallet_address = data.wallet_address
        db.commit()
        return {"message": "✅ Wallet linked successfully", "wallet_address": user.wallet_address}
    except Exception as e:
        logger.exception("Wallet linking failed")
        raise HTTPException(status_code=500, detail="Wallet linking failed")
    finally:
        db.close()

@app.post("/api/mine")
def mine(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.balance += 10
        db.commit()
        return {"message": "✅ You mined 10 coins", "balance": user.balance}
    except Exception as e:
        logger.exception("Mining failed")
        raise HTTPException(status_code=500, detail="Mining failed")
    finally:
        db.close()

@app.post("/api/spin")
def spin(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        prize = random.randint(1, 15)
        user.balance += prize
        db.commit()
        return {"message": f"🎰 Spin result: {prize} coins", "balance": user.balance}
    except Exception as e:
        logger.exception("Spin failed")
        raise HTTPException(status_code=500, detail="Spin failed")
    finally:
        db.close()

@app.post("/api/quest")
def quest(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        reward = random.randint(5, 20)
        user.balance += reward
        db.commit()
        return {"message": f"🎯 Quest complete! +{reward} coins", "balance": user.balance}
    except Exception as e:
        logger.exception("Quest failed")
        raise HTTPException(status_code=500, detail="Quest failed")
    finally:
        db.close()

@app.get("/balance")
def balance(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"balance": user.balance, "wallet": user.wallet_address or "Not linked"}
    finally:
        db.close()

# === TELEGRAM HANDLER ===
token = os.getenv("TELEGRAM_TOKEN")
telegram_app = None
if token:
    telegram_app = Application.builder().token(token).build()

    async def start(update, context):
        user_id = str(update.message.from_user.id)
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(telegram_id=user_id).first()
            if not user:
                user = User(telegram_id=user_id, balance=0)
                db.add(user)
                db.commit()
            url = "https://cryptominer-ui-two.vercel.app"
            keyboard = [[InlineKeyboardButton("Open App", web_app={"url": url})]]
            markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("👋 Welcome Henry!\n\nUse the commands below:\n/register - Create your account\n/mine - Start mining ⛏️\n/spin - Try your luck 🎰\n/quest - Complete a quest 🎯\n/balance - Check your wallet 💰\n/refer - Invite friends 👥 and earn rewards!", reply_markup=markup)
        finally:
            db.close()

    telegram_app.add_handler(CommandHandler("start", start))

    def run_bot():
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        telegram_app.run_polling()

    threading.Thread(target=run_bot, daemon=True).start()

# === MAIN ===
if __name__ == "__main__":
    logger.info("✅ Starting API on port 10000")
    uvicorn.run(app, host="0.0.0.0", port=10000)
