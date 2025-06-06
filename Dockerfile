FROM python:3.11-slim

WORKDIR /app

# Copy everything into /app
COPY . .

# Install requirements from the correct path
RUN pip install --no-cache-dir -r bot_service/requirements.txt

# Move into the bot_service folder
WORKDIR /app/bot_service

# Run the main app
CMD ["python", "main.py"]