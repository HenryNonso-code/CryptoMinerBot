FROM python:3.11-slim

WORKDIR /app

# Copy requirements.txt FIRST so it gets cached
COPY bot_service/requirements.txt /app/requirements.txt

# Then install dependencies
RUN pip install -r requirements.txt

# Copy all source code (main.py, bot.py, etc.)
COPY bot_service/app /app/app
COPY bot_service/bot.py /app/bot.py
COPY bot_service/main.py /app/main.py
COPY bot_service/users.db /app/users.db

CMD ["python", "main.py"]
