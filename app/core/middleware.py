"""
Error Handling Middleware and Exception Handlers

Provides:
- Global exception handling
- Request/response logging
- Performance monitoring
- Custom error responses
"""

import time
import traceback
from typing import Callable
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.json_logger import request_logger, error_logger, performance_logger
import logging

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for error handling and logging"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and handle errors"""
        start_time = time.time()
        
        # Log incoming request
        request_logger.log_request(
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            headers=dict(request.headers),
            client_ip=request.client.host if request.client else None
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            request_logger.log_response(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            # Add performance header
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            error_logger.log_error(
                error=e,
                context={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms
                }
            )
            
            # Return error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": str(e),
                    "path": request.url.path,
                    "timestamp": time.time()
                }
            )


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring endpoint performance"""
    
    def __init__(self, app, slow_threshold_ms: float = 1000.0):
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Monitor request performance"""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log slow requests
            if duration_ms > self.slow_threshold_ms:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path}",
                    extra={
                        "event_type": "slow_request",
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": round(duration_ms, 2),
                        "threshold_ms": self.slow_threshold_ms
                    }
                )
            
            return response
            
        except Exception:
            raise


# Custom Exception Classes

class RAGException(Exception):
    """Base exception for RAG application"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DocumentNotFoundException(RAGException):
    """Document not found exception"""
    
    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document not found: {document_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"document_id": document_id}
        )


class InvalidFileTypeException(RAGException):
    """Invalid file type exception"""
    
    def __init__(self, file_type: str, allowed_types: list):
        super().__init__(
            message=f"Invalid file type: {file_type}. Allowed: {', '.join(allowed_types)}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "file_type": file_type,
                "allowed_types": allowed_types
            }
        )


class FileTooLargeException(RAGException):
    """File too large exception"""
    
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            message=f"File too large: {file_size} bytes. Maximum: {max_size} bytes",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details={
                "file_size": file_size,
                "max_size": max_size
            }
        )


class EmbeddingGenerationException(RAGException):
    """Embedding generation failed exception"""
    
    def __init__(self, text: str, error: str):
        super().__init__(
            message=f"Failed to generate embedding: {error}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={
                "text_length": len(text),
                "error": error
            }
        )


class LLMInferenceException(RAGException):
    """LLM inference failed exception"""
    
    def __init__(self, model: str, error: str):
        super().__init__(
            message=f"LLM inference failed with {model}: {error}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={
                "model": model,
                "error": error
            }
        )


class VectorStoreException(RAGException):
    """Vector store operation failed exception"""
    
    def __init__(self, operation: str, error: str):
        super().__init__(
            message=f"Vector store {operation} failed: {error}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={
                "operation": operation,
                "error": error
            }
        )


# Exception Handlers

async def rag_exception_handler(request: Request, exc: RAGException):
    """Handler for RAG custom exceptions"""
    error_logger.log_error(
        error=exc,
        context={
            "path": request.url.path,
            "status_code": exc.status_code,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "timestamp": time.time()
        }
    )


async def validation_exception_handler(request: Request, exc: Exception):
    """Handler for validation exceptions"""
    error_logger.log_validation_error(
        field="request",
        message=str(exc)
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": str(exc),
            "path": request.url.path,
            "timestamp": time.time()
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handler for uncaught exceptions"""
    error_logger.log_error(
        error=exc,
        context={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "path": request.url.path,
            "timestamp": time.time()
        }
    )
