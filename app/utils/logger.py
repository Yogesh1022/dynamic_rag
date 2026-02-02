import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


class PlainFormatter(logging.Formatter):
    """Plain text formatter for human-readable logs."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging(
    log_level: str = None,
    log_format: str = None,
    log_file: str = None
) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ("json" or "plain")
        log_file: Path to log file (optional)
    """
    # Use settings if not provided
    log_level = log_level or settings.LOG_LEVEL
    log_format = log_format or settings.LOG_FORMAT
    log_file = log_file or settings.LOG_FILE
    
    # Convert log level string to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = PlainFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            # Create log directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
            root_logger.info(f"Logging to file: {log_file}")
        except Exception as e:
            root_logger.warning(f"Failed to create file handler: {e}")
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("multipart").setLevel(logging.WARNING)
    
    root_logger.info(f"Logging configured: level={log_level}, format={log_format}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_function_call(func):
    """
    Decorator to log function calls with arguments and return values.
    
    Usage:
        @log_function_call
        def my_function(arg1, arg2):
            return result
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(
            f"Calling {func.__name__}",
            extra={
                "function": func.__name__,
                "args": str(args)[:200],
                "kwargs": str(kwargs)[:200],
            }
        )
        
        try:
            result = func(*args, **kwargs)
            logger.debug(
                f"{func.__name__} completed",
                extra={
                    "function": func.__name__,
                    "result": str(result)[:200],
                }
            )
            return result
        except Exception as e:
            logger.error(
                f"{func.__name__} failed: {str(e)}",
                extra={
                    "function": func.__name__,
                    "error": str(e),
                },
                exc_info=True
            )
            raise
    
    return wrapper
