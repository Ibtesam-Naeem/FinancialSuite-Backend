import logging
import logging.handlers
import os
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
    
    def format(self, record):
        # Basic log data we always want
        log_data = {
            "time": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger_name": record.name,
            "msg": record.getMessage(),
            "path": record.module,
            # Add environment - useful for knowing where we're running
            "env": os.getenv("ENVIRONMENT", "dev")
        }
        
        # If there's an error, add the stack trace
        if record.exc_info:
            log_data["error"] = self.formatException(record.exc_info)
        
        # Add request_id if we have it
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        # Add any extra fields passed in the extra={} parameter
        if hasattr(record, "extras"):
            log_data.update(record.extras)

        return json.dumps(log_data)

def setup_logger(name=None):
    """Sets up logging how we want it:
    - Logs to console for local dev
    - JSON files for prod so we can search them
    - Rotates files so we don't fill up the disk
    """
    logger = logging.getLogger(name or "app")
    
    # Don't duplicate logs if logger already exists
    if logger.handlers:
        return logger
    
    # Default to INFO, use DEBUG in dev
    if os.getenv("ENVIRONMENT") == "dev":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Console output - nice for development
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        '%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(console)

    # File output - JSON for easier searching in prod
    try:
        log_dir = os.getenv("LOG_DIR", "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.handlers.RotatingFileHandler(
            f"{log_dir}/{name or 'app'}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3  # Keep 3 backup files
        )
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    except Exception as e:
        # Don't crash if we can't write to files
        logger.warning(f"Couldn't set up file logging: {e}")
    
    return logger

def get_request_logger(base_logger, req_id):
    """
    Adds request ID to logs so we can trace requests.
    Just creates a child logger with the ID attached.
    """
    logger = logging.getLogger(f"{base_logger.name}.{req_id}")
    logger.request_id = req_id  # We'll use this in the formatter
    return logger
