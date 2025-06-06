FROM python:3.11-slim

WORKDIR /app

# Copy requirements from bot_service folder
COPY bot_service/requirements.txt ./requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy full code
COPY bot_service/ .

# ✅ Run FastAPI app
CMD ["python", "./main.py"]
