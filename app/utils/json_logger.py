"""
Structured JSON Logging Configuration

Provides:
- JSON formatted logs
- Request/response logging
- Performance metrics
- Error tracking
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record: Dict, record: logging.LogRecord, message_dict: Dict):
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add module and function
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        
        # Add line number
        log_record['line'] = record.lineno
        
        # Add process/thread info
        log_record['process_id'] = record.process
        log_record['thread_id'] = record.thread


class RequestLogger:
    """Logger for HTTP requests"""
    
    @staticmethod
    def log_request(
        method: str,
        path: str,
        query_params: Dict = None,
        headers: Dict = None,
        client_ip: str = None
    ):
        """Log incoming request"""
        logger = logging.getLogger("rag.request")
        logger.info(
            "Incoming request",
            extra={
                "event_type": "http_request",
                "method": method,
                "path": path,
                "query_params": query_params or {},
                "client_ip": client_ip,
                "user_agent": headers.get("user-agent") if headers else None
            }
        )
    
    @staticmethod
    def log_response(
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        response_size: int = None
    ):
        """Log outgoing response"""
        logger = logging.getLogger("rag.response")
        logger.info(
            "Response sent",
            extra={
                "event_type": "http_response",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "response_size": response_size
            }
        )


class PerformanceLogger:
    """Logger for performance metrics"""
    
    @staticmethod
    def log_operation(
        operation: str,
        duration_ms: float,
        success: bool,
        metadata: Dict = None
    ):
        """Log operation performance"""
        logger = logging.getLogger("rag.performance")
        logger.info(
            f"Operation: {operation}",
            extra={
                "event_type": "performance",
                "operation": operation,
                "duration_ms": round(duration_ms, 2),
                "success": success,
                "metadata": metadata or {}
            }
        )
    
    @staticmethod
    def log_db_query(
        query_type: str,
        duration_ms: float,
        row_count: int = None
    ):
        """Log database query"""
        logger = logging.getLogger("rag.database")
        logger.info(
            f"DB Query: {query_type}",
            extra={
                "event_type": "database_query",
                "query_type": query_type,
                "duration_ms": round(duration_ms, 2),
                "row_count": row_count
            }
        )
    
    @staticmethod
    def log_llm_call(
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float
    ):
        """Log LLM API call"""
        logger = logging.getLogger("rag.llm")
        logger.info(
            f"LLM Call: {model}",
            extra={
                "event_type": "llm_call",
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "duration_ms": round(duration_ms, 2)
            }
        )


class ErrorLogger:
    """Logger for errors and exceptions"""
    
    @staticmethod
    def log_error(
        error: Exception,
        context: Dict = None,
        user_id: str = None
    ):
        """Log application error"""
        logger = logging.getLogger("rag.error")
        logger.error(
            f"Error: {type(error).__name__}",
            extra={
                "event_type": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {},
                "user_id": user_id
            },
            exc_info=True
        )
    
    @staticmethod
    def log_validation_error(
        field: str,
        message: str,
        value: Any = None
    ):
        """Log validation error"""
        logger = logging.getLogger("rag.validation")
        logger.warning(
            f"Validation error: {field}",
            extra={
                "event_type": "validation_error",
                "field": field,
                "message": message,
                "value": str(value) if value else None
            }
        )


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """
    Configure structured JSON logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logs
    """
    # Create formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Create specific loggers
    for logger_name in [
        "rag.request",
        "rag.response", 
        "rag.performance",
        "rag.database",
        "rag.llm",
        "rag.error",
        "rag.validation"
    ]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper()))
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    
    logging.info("✅ Structured JSON logging configured")


# Convenience exports
request_logger = RequestLogger()
performance_logger = PerformanceLogger()
error_logger = ErrorLogger()
