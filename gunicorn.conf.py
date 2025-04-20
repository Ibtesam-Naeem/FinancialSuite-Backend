# Gunicorn configuration file
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 2  # Start with a smaller number for debugging
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 2

# Create log directory if it doesn't exist
os.makedirs("/app/logs", exist_ok=True)

# Logging
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = "debug"  # Temporarily set to debug for more info
capture_output = True
enable_stdio_inheritance = True

# Process naming
proc_name = "market_dashboard"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Debugging
reload = False
preload_app = True

# Application module
pythonpath = '/app' 