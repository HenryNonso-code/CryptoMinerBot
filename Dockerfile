FROM python:3.11-slim

WORKDIR /app

# ✅ Copy the requirements.txt from bot_service directory explicitly
COPY bot_service/requirements.txt /app/requirements.txt

# ✅ Install dependencies
RUN pip install -r requirements.txt

# ✅ Now copy the entire bot_service app code into /app
COPY bot_service/ .

# ✅ Run the main FastAPI app
CMD ["python", "main.py"]
