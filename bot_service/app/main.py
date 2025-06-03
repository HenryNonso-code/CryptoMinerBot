from fastapi import FastAPI
from telegram.ext import Application, CommandHandler
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import uvicorn
import threading

app = FastAPI()

# Health check endpoint
@app.get("/")
@app.head("/")
async def root():
    return {"message": "CryptoMinerBot is running!"}

# Database setup (SQLite with users.db)
engine = create_engine("sqlite:///users.db", echo=True)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    telegram_id = Column(String, primary_key=True)
    balance = Column(Integer, default=0)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Telegram bot setup
token = os.getenv("TELEGRAM_TOKEN")
if not token:
    raise ValueError("TELEGRAM_TOKEN environment variable not set")

telegram_app = Application.builder().token(token).build()

# Command handlers
async def start(update, context):
    user_id = str(update.message.from_user.id)
    user = session.query(User).filter_by(telegram_id=user_id).first()
    if not user:
        user = User(telegram_id=user_id, balance=0)
        session.add(user)
        session.commit()
    await update.message.reply_text("Welcome to CryptoMinerBot! Use /mine to start mining.")

async def mine(update, context):
    user_id = str(update.message.from_user.id)
    user = session.query(User).filter_by(telegram_id=user_id).first()
    if not user:
        await update.message.reply_text("Please use /start first!")
        return
    user.balance += 10  # Simulate mining by adding 10 points
    session.commit()
    await update.message.reply_text(f"Mining successful! Your balance: {user.balance} points.")

async def balance(update, context):
    user_id = str(update.message.from_user.id)
    user = session.query(User).filter_by(telegram_id=user_id).first()
    if not user:
        await update.message.reply_text("Please use /start first!")
        return
    await update.message.reply_text(f"Your balance: {user.balance} points.")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("mine", mine))
telegram_app.add_handler(CommandHandler("balance", balance))

# Run Telegram bot in a separate thread
def run_telegram_bot():
    telegram_app.run_polling()

threading.Thread(target=run_telegram_bot, daemon=True).start()

# Run FastAPI server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)