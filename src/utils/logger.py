import logging
import sys

def setup_logger(name=None):
    """
    Simple logger that outputs to stdout for Digital Ocean container logs.
    since digital Ocean App Platform automatically collects stdout/stderr.
    """
    logger = logging.getLogger(name or "app")
    
    if logger.handlers:
        return logger
    
    handler = logging.StreamHandler(sys.stdout)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    return logger

# ---------------------------- END OF FILE ----------------------------