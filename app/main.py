from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import (
    RAGException,
    rag_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from app.core.middleware import (
    ErrorHandlingMiddleware,
    PerformanceMonitoringMiddleware,
    rag_exception_handler as middleware_rag_handler,
    validation_exception_handler as middleware_validation_handler,
    generic_exception_handler,
)
from app.api.v1.api import api_router
from app.api.deps import close_db_connections
from app.services.cache import cache_service
from app.utils.json_logger import setup_logging

# Configure structured JSON logging
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file="./logs/app.log" if settings.APP_ENV == "production" else None
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting up Dynamic RAG System...")
    logger.info(f"📦 Environment: {settings.APP_ENV}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    
    # Create directories
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path("./logs").mkdir(parents=True, exist_ok=True)
    
    # Connect to Redis cache
    try:
        await cache_service.connect()
        logger.info("✅ Cache service connected")
    except Exception as e:
        logger.warning(f"⚠️  Cache service unavailable: {e}")
    
    logger.info("✅ Startup complete!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    await close_db_connections()
    
    # Disconnect cache
    try:
        await cache_service.disconnect()
        logger.info("Cache service disconnected")
    except Exception as e:
        logger.warning(f"Error disconnecting cache: {e}")
    
    logger.info("✅ Shutdown complete!")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Industry-grade RAG system with Ollama, Qdrant, and PostgreSQL",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Performance monitoring middleware
app.add_middleware(
    PerformanceMonitoringMiddleware,
    slow_threshold_ms=1000.0  # Log requests slower than 1 second
)

# Error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Exception handlers (using middleware handlers)
app.add_exception_handler(RAGException, middleware_rag_handler)
app.add_exception_handler(RequestValidationError, middleware_validation_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint with cache stats."""
    # Get cache statistics
    cache_stats = await cache_service.get_stats()
    
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "cache": cache_stats
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
