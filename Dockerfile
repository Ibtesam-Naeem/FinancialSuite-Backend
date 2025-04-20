# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Installs the system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements first to leverage Docker cache
COPY requirements.txt .

# Installs the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Installs the Playwright browsers
RUN playwright install chromium

# Copies the rest of the application
COPY . .

# Creates the logs directory
RUN mkdir -p logs

# Sets the environment variables
ENV ENVIRONMENT=production
ENV LOG_DIR=/app/logs

# Expose port
EXPOSE 8000

# Start the application with Gunicorn
CMD ["gunicorn", "src.main:app", "--config", "gunicorn.conf.py"] 