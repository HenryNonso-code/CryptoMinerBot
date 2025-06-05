FROM python:3.11-slim

WORKDIR /app

# Step 1: Copy everything including bot_service (before pip install)
COPY . .

# Step 2: Install dependencies from the copied requirements.txt
RUN pip install --no-cache-dir -r bot_service/requirements.txt

# Step 3: Run main.py from bot_service
CMD ["python", "bot_service/main.py"]
