import logging
import os
import random
import threading
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI App ===
app = FastAPI()

# === DB Setup ===
# Delete old DB to apply schema changes (TEMPORARY)
if os.path.exists("users.db"):
    os.remove("users.db")

engine = create_engine("sqlite:///users.db", echo=True)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    telegram_id = Column(String, primary_key=True)
    balance = Column(Integer, default=0)
    wallet_address = Column(String, nullable=True)  # 👈 Added this

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

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
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            user = User(telegram_id=user_id, balance=0)
            session.add(user)
            session.commit()
            logger.info(f"New user registered: {user_id}")
        keyboard = [[InlineKeyboardButton("Open Mining Dashboard", web_app={"url": "https://crypto-miner-bot-web.onrender.com/miniapp"})]]
        markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Welcome to CryptoMinerBot! Open your mining dashboard below:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Error in /start: {e}")
        await update.message.reply_text("An error occurred. Try again later.")

async def mine(update, context):
    user_id = str(update.message.from_user.id)
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("Use /start first.")
            return
        user.balance += 10
        session.commit()
        await update.message.reply_text(f"✅ You mined 10 coins!\nNew balance: {user.balance}")
    except Exception as e:
        logger.error(f"Mine error: {e}")
        await update.message.reply_text("An error occurred.")

async def balance(update, context):
    user_id = str(update.message.from_user.id)
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("Use /start first.")
            return
        await update.message.reply_text(f"💰 Your balance: {user.balance}")
    except Exception as e:
        logger.error(f"Balance error: {e}")
        await update.message.reply_text("Could not fetch balance.")

async def spin(update, context):
    user_id = str(update.message.from_user.id)
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("Use /start first.")
            return
        win = random.randint(1, 10)
        user.balance += win
        session.commit()
        await update.message.reply_text(f"🎰 Spin result: {win}\nNew balance: {user.balance}")
    except Exception as e:
        logger.error(f"Spin error: {e}")
        await update.message.reply_text("Could not spin.")

async def quest(update, context):
    user_id = str(update.message.from_user.id)
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("Use /start first.")
            return
        reward = random.randint(5, 15)
        user.balance += reward
        session.commit()
        await update.message.reply_text(f"🎯 Quest complete!\nEarned: {reward}\nBalance: {user.balance}")
    except Exception as e:
        logger.error(f"Quest error: {e}")
        await update.message.reply_text("Error during quest.")

# === Mini-App API Endpoints ===
@app.get("/")
@app.head("/")
def health():
    return {"message": "CryptoMinerBot is running"}

@app.get("/api/user/{telegram_id}")
def get_user(telegram_id: str):
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"balance": user.balance, "wallet_address": user.wallet_address}

@app.get("/api/mine/{telegram_id}")
def api_mine(telegram_id: str):
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.balance += 10
    session.commit()
    return {"balance": user.balance}

# ✅ NEW: /link-wallet route
class WalletLinkRequest(BaseModel):
    telegram_id: str
    wallet_address: str

@app.post("/link-wallet")
def link_wallet(data: WalletLinkRequest):
    try:
        user = session.query(User).filter_by(telegram_id=data.telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.wallet_address = data.wallet_address
        session.commit()
        return {"message": "✅ Wallet linked successfully", "wallet_address": user.wallet_address}
    except Exception as e:
        logger.error(f"Link wallet error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")

# === MiniApp Landing Page ===
@app.get("/miniapp")
def miniapp():
    return HTMLResponse("<h1>✅ CryptoMinerBot MiniApp Connected</h1>")

# === Start Bot Polling ===
if telegram_app:
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("mine", mine))
    telegram_app.add_handler(CommandHandler("balance", balance))
    telegram_app.add_handler(CommandHandler("spin", spin))
    telegram_app.add_handler(CommandHandler("quest", quest))

    def run_bot():
        telegram_app.run_polling()

    threading.Thread(target=run_bot, daemon=True).start()
else:
    logger.warning("Telegram bot not started.")

# === Run FastAPI ===
if __name__ == "__main__":
    logger.info("Starting server on http://0.0.0.0:10000")
    uvicorn.run(app, host="0.0.0.0", port=10000)
