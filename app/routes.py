# app/routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from pydantic import BaseModel

router = APIRouter()

class RegisterRequest(BaseModel):
    telegram_id: str
    referral_code: str | None = None

@router.post("/register")
def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(telegram_id=data.telegram_id).first()
    if not user:
        referral_code = f"{data.telegram_id[-6:]}_{User.generate_suffix()}"
        user = User(telegram_id=data.telegram_id, referral_code=referral_code, referred_by=data.referral_code)
        db.add(user)
        db.commit()
    return {
        "message": "✅ Registered",
        "id": user.id,
        "referral_code": user.referral_code,
        "balance": user.balance
    }

@router.post("/mine")
def mine(data: RegisterRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(telegram_id=data.telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    coins = User.generate_coins()
    user.balance += coins
    db.commit()
    return {"coins": coins, "balance": user.balance}

@router.post("/spin")
def spin(data: RegisterRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(telegram_id=data.telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    amount = User.spin()
    user.balance += amount
    db.commit()
    return {"amount": amount, "balance": user.balance}

@router.get("/balance")
def get_balance(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"balance": user.balance, "referral_code": user.referral_code}
