import uuid
import time
from contextlib import contextmanager
from typing import Generator
from loguru import logger
import sys

# Remove default logger and configure loguru
logger.remove()

# Add structured JSON logging to stderr
logger.add(
    sys.stderr,
    format="{time} | {level} | {extra[request_id]} | {message}",
    level="INFO",
    serialize=True  # Enable JSON structured logging
)

@contextmanager
def log_request(request_id: str = None) -> Generator[str, None, None]:
    """Context manager to add request_id to log context"""
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    # Bind request_id to logger context
    with logger.bind(request_id=request_id):
        yield request_id

def get_logger():
    """Get the configured logger instance"""
    return logger

# Request timing decorator
def log_request_timing(func):
    """Decorator to log request timing"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"Request completed",
                extra={
                    "function": func.__name__,
                    "duration_ms": round(duration_ms, 2)
                }
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "function": func.__name__,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e)
                }
            )
            raise
    return wrapper
