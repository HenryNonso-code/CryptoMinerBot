from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.db import get_db, init_db
from app.models import User
from datetime import datetime, timedelta
from pydantic import BaseModel
import random

app = FastAPI(
    title="CryptoMinerBot API",
    version="1.0.0",
    description="FastAPI backend for the Crypto Telegram mining bot."
)

# Allow all CORS (for future frontend use)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()  # Ensure DB is initialized

# === Pydantic Model for Registration ===
class RegisterRequest(BaseModel):
    referral_code: str | None = None

# === Utility ===
def get_or_create_user(db: Session, telegram_id: str, username: str = "Anonymous", referred_by: str = None):
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        referral_code = f"{username.lower()}_{random.randint(1000,9999)}"
        user = User(
            telegram_id=telegram_id,
            username=username,
            referral_code=referral_code,
            referred_by=referred_by,
            balance=0,
            last_mined=None,
            last_spun=None,
            referral_points=0,
            quests_completed=""
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        if referred_by:
            referrer = db.query(User).filter_by(referral_code=referred_by).first()
            if referrer:
                referrer.balance += 5
                referrer.referral_points += 1
                user.balance += 2  # bonus for referred user
                db.commit()
    return user

# === Routes ===
@app.post("/register")
def register(
    telegram_id: str,
    username: str = "Anonymous",
    req: RegisterRequest = None,
    db: Session = Depends(get_db)
):
    referral_code = req.referral_code if req else None
    user = get_or_create_user(db, telegram_id, username, referral_code)
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "referral_code": user.referral_code,
        "balance": round(user.balance, 2),
        "referrals": user.referral_points,
        "message": "User registered successfully"
    }

@app.post("/mine")
def mine(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.utcnow()
    if user.last_mined and now - user.last_mined < timedelta(hours=12):
        remaining = timedelta(hours=12) - (now - user.last_mined)
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        return {
            "message": f"⏳ Already mined. Come back in {hours}h {minutes}m.",
            "user_id": user.telegram_id,
            "balance": round(user.balance, 5),
            "referral_code": user.referral_code
        }

    reward = round(random.uniform(0.005, 0.02), 5)
    user.balance += reward
    user.last_mined = now
    db.commit()
    return {"amount": reward, "balance": round(user.balance, 5)}

@app.post("/spin")
def spin(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.utcnow()
    if user.last_spun and now - user.last_spun < timedelta(hours=24):
        remaining = timedelta(hours=24) - (now - user.last_spun)
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        return {
            "message": f"⏳ Already spun. Try again in {hours}h {minutes}m.",
            "balance": round(user.balance, 5)
        }

    amount = round(random.uniform(0, 5), 3)
    user.balance += amount
    user.last_spun = now
    user.last_spin_reward = amount
    db.commit()
    return {"amount": amount, "balance": round(user.balance, 5)}

@app.post("/quest")
def quest(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reward = round(random.uniform(0.01, 0.05), 4)
    user.balance += reward
    db.commit()
    return {"amount": reward, "balance": round(user.balance, 5)}

@app.get("/balance")
def balance(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "balance": round(user.balance, 5),
        "referral_code": user.referral_code,
        "referrals": user.referral_points
    }
