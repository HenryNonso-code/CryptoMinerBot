FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy everything into /app (this includes main.py and requirements.txt)
COPY bot_service/ /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the FastAPI app
CMD ["python", "main.py"]
