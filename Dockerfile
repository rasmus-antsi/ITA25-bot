# Use official Python slim image
FROM python:3.11-slim

WORKDIR /app

# Upgrade pip first
RUN python -m pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Set environment variable for data directory
ENV DATA_DIR=/app/data

# Ensure data directory has proper permissions
RUN chmod 755 /app/data

CMD ["python", "main.py"]
