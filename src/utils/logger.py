import logging
import logging.handlers
import os
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
    
    def format(self, record):
        """
        Basic log data
        """
        log_data = {
            "time": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger_name": record.name,
            "msg": record.getMessage(),
            "path": record.module,
            "env": os.getenv("ENVIRONMENT", "dev")
        }
        
        if record.exc_info:
            log_data["error"] = self.formatException(record.exc_info)
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        if hasattr(record, "extras"):
            log_data.update(record.extras)

        return json.dumps(log_data)

def setup_logger(name=None):
    """
    Sets up logging:
    - Logs to console for local dev
    - JSON files for prod so we can search them
    - Rotates files so we don't fill up the disk
    """
    logger = logging.getLogger(name or "app")
    
    if logger.handlers:
        return logger
    
    # Always add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    if os.getenv("ENVIRONMENT") == "dev":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        # Add file handler for production
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, "app.log"),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger

def get_request_logger(base_logger, req_id):
    """
    Adds request ID to logs so we can trace requests.
    Just creates a child logger with the ID attached.
    """
    logger = logging.getLogger(f"{base_logger.name}.{req_id}")
    logger.request_id = req_id
    return logger
