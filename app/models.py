# app/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=True)
    balance = Column(Float, default=0)
    referral_code = Column(String, unique=True, nullable=True)
    referred_by = Column(String, nullable=True)
    last_mined = Column(DateTime, nullable=True)
    last_spun = Column(DateTime, nullable=True)
    last_spin_reward = Column(Float, default=0)
    quests_completed = Column(String, default="")
    referral_points = Column(Integer, default=0)
    wallet_address = Column(String, nullable=True)
