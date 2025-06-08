# Dockerfile

# Use slim Python 3.11 base image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (optional but helpful)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY bot_service/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY bot_service/ ./bot_service

# Run the FastAPI app (main.py)
CMD ["python", "bot_service/main.py"]
