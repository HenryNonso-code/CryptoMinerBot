FROM python:3.11-slim

WORKDIR /app

# Copy everything
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r bot_service/requirements.txt

# Run FastAPI app
CMD ["python", "bot_service/main.py"]