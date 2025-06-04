FROM python:3.11-slim

WORKDIR /app

# ✅ Correct path to the actual file inside your repo
COPY bot_service/requirements.txt .

# ✅ Install dependencies properly
RUN pip install -r requirements.txt

# ✅ Copy the rest of your app (main.py, bot.py, etc.)
COPY bot_service/ .

# ✅ Run the FastAPI + Telegram bot hybrid script
CMD ["python", "main.py"]
