FROM python:3.11-slim

WORKDIR /app

# ✅ Copy ONLY the requirements.txt file FIRST
COPY bot_service/requirements.txt .

# ✅ Install dependencies before copying rest
RUN pip install -r requirements.txt

# ✅ Now copy your full codebase
COPY bot_service/ .

# ✅ Run your FastAPI + Telegram hybrid bot
CMD ["python", "main.py"]
