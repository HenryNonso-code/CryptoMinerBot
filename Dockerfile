FROM python:3.11-slim

WORKDIR /app

# Copy everything in the repo (which includes requirements.txt and main.py)
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the app
CMD ["python", "main.py"]
