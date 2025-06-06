FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies
COPY bot_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire bot_service project into container
COPY bot_service/ ./bot_service

# ✅ Correct path to run main.py
CMD ["python", "bot_service/main.py"]
