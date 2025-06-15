# Root-level Dockerfile for CryptoMinerBot-1
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Create /data directory for mounted persistent storage (required by SQLite)
RUN mkdir -p /data

# Copy all project files into container
COPY . .

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose the FastAPI app port
EXPOSE 10000

# Run the FastAPI app using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
