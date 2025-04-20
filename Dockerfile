# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright and Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y \
    google-chrome-stable \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Copy the requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright CLI and browser
RUN pip install playwright && playwright install chromium && playwright install-deps chromium

# Copy the rest of the application
COPY . .

# Set environment variables
ENV ENVIRONMENT=production
ENV LOG_DIR=/app/logs
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Start the application with Gunicorn
CMD ["gunicorn", "main:app", "--config", "gunicorn.conf.py"] 