# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# System dependencies (optional)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirement file and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose port for FastAPI
EXPOSE 10000

# Start FastAPI + Telegram bot
CMD ["python", "main.py"]
