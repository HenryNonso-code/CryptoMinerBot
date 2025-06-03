FROM python:3.11-slim

WORKDIR /app

# ✅ Copy requirements.txt before install
COPY requirements.txt .

# ✅ Then install packages
RUN pip install -r requirements.txt

# ✅ Now copy your app code
COPY bot_service/app /app
COPY users.db /app

# ✅ Start the app
CMD ["python", "main.py"]
