
import os, random, datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# === DB Setup ===
Base = declarative_base()
engine = create_engine("sqlite:////data/users.db", echo=True, connect_args={"check_same_thread": False})
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

# === FastAPI App ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Models ===
class RegisterRequest(BaseModel):
    telegram_id: str
    username: str = "User"
    referral_code: str | None = None

@app.get("/")
def root():
    return {"message": "✅ CryptoMiner API is running"}

@app.post("/register")
def register_user(req: RegisterRequest):
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
def mine(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not registered")
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
def spin(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not registered")
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
def quest(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not registered")
        reward = random.randint(2, 12)
        user.balance += reward
        user.quests_completed = (user.quests_completed or "") + f",Q{random.randint(1,100)}"
        db.commit()
        return {"message": "Quest complete", "amount": reward, "balance": user.balance}
    finally:
        db.close()

@app.get("/balance")
def balance(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not registered")
        return {"balance": user.balance, "referral_code": user.referral_code, "referrals": 0}
    finally:
        db.close()
