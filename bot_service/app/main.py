import logging
import os
import random
import threading
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI setup
app = FastAPI()

# Health check endpoint
@app.get("/")
@app.head("/")
async def root():
    logger.info("Received request for / endpoint")
    return {"message": "CryptoMinerBot is running!"}

# Database setup (SQLite with users.db)
try:
    engine = create_engine("sqlite:///users.db", echo=True)
    Base = declarative_base()

    class User(Base):
        __tablename__ = "users"
        telegram_id = Column(String, primary_key=True)
        balance = Column(Integer, default=0)

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# Telegram bot setup
token = os.getenv("TELEGRAM_TOKEN")
telegram_app = None
if token:
    try:
        telegram_app = Application.builder().token(token).build()
        logger.info("Telegram bot initialized successfully")
    except Exception as e:
        logger.error(f"Telegram bot initialization failed: {e}")
else:
    logger.error("TELEGRAM_TOKEN environment variable not set")

# Command handlers
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
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Welcome to CryptoMinerBot! Open your mining dashboard below:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in /start command: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")

async def mine(update, context):
    user_id = str(update.message.from_user.id)
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("Please use /start first!")
            return
        user.balance += 10
        session.commit()
        logger.info(f"User {user_id} mined 10 points. New balance: {user.balance}")
        await update.message.reply_text(f"Mining successful! Your balance: {user.balance} coins.")
    except Exception as e:
        logger.error(f"Error in /mine command: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")

async def balance(update, context):
    user_id = str(update.message.from_user.id)
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("Please use /start first!")
            return
        await update.message.reply_text(f"Your balance: {user.balance} coins.")
    except Exception as e:
        logger.error(f"Error in /balance command: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")

async def spin(update, context):
    user_id = str(update.message.from_user.id)
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("Please use /start first!")
            return
        spin_result = random.uniform(1, 10)
        user.balance += int(spin_result)
        session.commit()
        logger.info(f"User {user_id} spun and earned {spin_result:.1f} coins. New balance: {user.balance}")
        await update.message.reply_text(f"Spin result: {spin_result:.1f} coins\nNew balance: {user.balance} coins.")
    except Exception as e:
        logger.error(f"Error in /spin command: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")

async def quest(update, context):
    user_id = str(update.message.from_user.id)
    try:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await update.message.reply_text("Please use /start first!")
            return
        quest_reward = random.randint(5, 15)
        user.balance += quest_reward
        session.commit()
        logger.info(f"User {user_id} completed a quest and earned {quest_reward} coins. New balance: {user.balance}")
        await update.message.reply_text(f"Quest completed!\nEarned: {quest_reward} coins\nNew balance: {user.balance} coins.")
    except Exception as e:
        logger.error(f"Error in /quest command: {e}")
        await update.message.reply_text("An error occurred. Please try again later.")

# API endpoints for the mini-app
@app.get("/api/user/{telegram_id}")
async def get_user(telegram_id: str):
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"balance": user.balance}
    except Exception as e:
        logger.error(f"Error in /api/user/{telegram_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/mine/{telegram_id}")
async def api_mine(telegram_id: str):
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.balance += 10
        session.commit()
        logger.info(f"User {telegram_id} mined 10 points via API. New balance: {user.balance}")
        return {"balance": user.balance}
    except Exception as e:
        logger.error(f"Error in /api/mine/{telegram_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Serve the mini-app HTML
@app.get("/miniapp")
async def miniapp():
    logger.info("Serving mini-app HTML")
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>CryptoMinerBot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 500px;
                margin: 0 auto;
                padding: 20px;
            }
            .balance {
                font-size: 36px;
                color: #2c3e50;
            }
            .timer {
                font-size: 24px;
                color: #e74c3c;
            }
            .multiplier {
                font-size: 20px;
                color: #3498db;
            }
            .tabs {
                display: flex;
                justify-content: space-around;
                margin: 20px 0;
            }
            .tab {
                padding: 10px 20px;
                background: #3498db;
                color: white;
                border-radius: 5px;
                cursor: pointer;
            }
            .tab:hover {
                background: #2980b9;
            }
            .button {
                padding: 10px 20px;
                background: #e67e22;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            .button:hover {
                background: #d35400;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CryptoMinerBot</h1>
            <div class="balance" id="balance">0</div>
            <div class="timer" id="timer">00:00:00</div>
            <div class="multiplier" id="multiplier">x1</div>
            <div class="tabs">
                <div class="tab" onclick="showTab('home')">Home</div>
                <div class="tab" onclick="showTab('tasks')">Tasks</div>
                <div class="tab" onclick="showTab('ads')">Ads</div>
                <div class="tab" onclick="showTab('activity')">Activity</div>
                <div class="tab" onclick="showTab('earn')">Earn</div>
                <div class="tab" onclick="showTab('wallet')">Wallet</div>
            </div>
            <div id="content">
                <button class="button" onclick="mine()">Mine</button>
            </div>
        </div>

        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script>
            let balance = 0;
            let multiplier = 1;
            let timer = 3600;

            function updateBalance(newBalance) {
                balance = newBalance;
                document.getElementById('balance').innerText = balance.toLocaleString();
            }

            function updateTimer() {
                if (timer <= 0) {
                    timer = 3600;
                    multiplier = Math.min(multiplier + 1, 8);
                    updateMultiplier();
                }
                let hours = Math.floor(timer / 3600);
                let minutes = Math.floor((timer % 3600) / 60);
                let seconds = timer % 60;
                document.getElementById('timer').innerText = 
                    `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                timer--;
            }

            function updateMultiplier() {
                document.getElementById('multiplier').innerText = `x${multiplier}`;
            }

            function mine() {
                const userId = Telegram.WebApp.initDataUnsafe.user.id;
                fetch(`/api/mine/${userId}`)
                    .then(response => response.json())
                    .then(data => {
                        updateBalance(data.balance);
                    })
                    .catch(error => {
                        console.error('Error mining:', error);
                        alert('Error mining. Please try again.');
                    });
            }

            function showTab(tab) {
                document.getElementById('content').innerHTML = `<h2>${tab.charAt(0).toUpperCase() + tab.slice(1)}</h2>`;
                if (tab === 'home') {
                    document.getElementById('content').innerHTML += '<button class="button" onclick="mine()">Mine</button>';
                } else if (tab === 'wallet') {
                    document.getElementById('content').innerHTML += `<p>Your balance: ${balance.toLocaleString()} coins</p>`;
                }
            }

            Telegram.WebApp.ready();
            const userId = Telegram.WebApp.initDataUnsafe.user.id;
            fetch(`/api/user/${userId}`)
                .then(response => response.json())
                .then(data => {
                    updateBalance(data.balance);
                    updateMultiplier();
                    setInterval(updateTimer, 1000);
                    showTab('home');
                })
                .catch(error => {
                    console.error('Error fetching user data:', error);
                    alert('Error loading user data.');
                });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Register command handlers if Telegram bot is initialized
if telegram_app:
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("mine", mine))
    telegram_app.add_handler(CommandHandler("balance", balance))
    telegram_app.add_handler(CommandHandler("spin", spin))
    telegram_app.add_handler(CommandHandler("quest", quest))

    # Run Telegram bot in a separate thread
    def run_telegram_bot():
        logger.info("Starting Telegram bot polling")
        telegram_app.run_polling()

    threading.Thread(target=run_telegram_bot, daemon=True).start()
else:
    logger.warning("Telegram bot not initialized; skipping polling")

# Run FastAPI server
if __name__ == "__main__":
    logger.info("Starting FastAPI server on http://0.0.0.0:10000")
    uvicorn.run(app, host="0.0.0.0", port=10000)