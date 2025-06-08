# Use a minimal Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all files to the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose FastAPI port
EXPOSE 10000

# Start the FastAPI + Telegram app from app/main.py
CMD ["python", "app/main.py"]
