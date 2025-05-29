from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import random

from app.db import get_db, init_db

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# === Pydantic Models ===
class RegisterRequest(BaseModel):
    telegram_id: str
    referral_code: str | None = None


# === Utility ===
def get_or_create_user(db: Session, telegram_id: str, referral_code: str = None):
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            referral_code=f"{telegram_id[-6:]}_{random.randint(1000, 9999)}",
            referred_by=referral_code,
            balance=0,
            last_mined=None,
            last_spun=None,
            last_spin_reward=0,
            referral_points=0,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# === Endpoints ===
@app.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = get_or_create_user(db, payload.telegram_id, payload.referral_code)

    # Award referral if valid
    if payload.referral_code and user.referred_by == payload.referral_code:
        referrer = db.query(User).filter_by(referral_code=payload.referral_code).first()
        if referrer and referrer.telegram_id != payload.telegram_id:
            referrer.referral_points += 10
            referrer.balance += 5
            db.commit()

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "referral_code": user.referral_code,
        "balance": round(user.balance, 2),
        "message": "User registered successfully",
    }


@app.post("/mine")
def mine(telegram_id: str, db: Session = Depends(get_db)):
    user = get_or_create_user(db, telegram_id)
    now = datetime.utcnow()

    if user.last_mined and (now - user.last_mined).seconds < 10:
        raise HTTPException(status_code=429, detail="Mine cooldown in effect")

    amount = random.uniform(1, 10)
    user.balance += amount
    user.last_mined = now
    db.commit()

    return {"amount": round(amount, 2), "balance": round(user.balance, 2)}


@app.post("/spin")
def spin(telegram_id: str, db: Session = Depends(get_db)):
    user = get_or_create_user(db, telegram_id)
    now = datetime.utcnow()

    if user.last_spun and (now - user.last_spun).seconds < 30:
        raise HTTPException(status_code=429, detail="Spin cooldown in effect")

    amount = random.uniform(0, 20)
    user.balance += amount
    user.last_spun = now
    user.last_spin_reward = amount
    db.commit()

    return {"amount": round(amount, 2), "balance": round(user.balance, 2)}


@app.post("/quest")
def quest(telegram_id: str, db: Session = Depends(get_db)):
    user = get_or_create_user(db, telegram_id)
    amount = random.uniform(3, 12)
    user.balance += amount
    db.commit()

    return {"amount": round(amount, 2), "balance": round(user.balance, 2)}


@app.get("/balance")
def balance(telegram_id: str, db: Session = Depends(get_db)):
    user = get_or_create_user(db, telegram_id)
    return {
        "balance": round(user.balance, 2),
        "referral_code": user.referral_code,
        "referrals": user.referral_points,
    }
