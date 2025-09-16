# Use official Python slim image
FROM python:3.11-slim

WORKDIR /app

# Upgrade pip first
RUN python -m pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
