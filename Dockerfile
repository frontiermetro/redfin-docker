FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y wget gnupg ca-certificates curl unzip fonts-liberation libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxrandr2 libgbm1 libgtk-3-0 libasound2 libxdamage1 libxfixes3 libx11-xcb1 libxext6 libx11-6 libxss1 xvfb

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its dependencies
RUN playwright install --with-deps chromium

# Copy app
COPY . .

# Expose port and run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]