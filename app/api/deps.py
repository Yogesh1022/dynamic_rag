from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.exceptions import VectorStoreException
import logging

logger = logging.getLogger(__name__)

# Database Base
Base = declarative_base()

# Database Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# Session Factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Qdrant Client (singleton)
_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """
    Get or create Qdrant client.
    
    Usage:
        @app.get("/search")
        async def search(qdrant: QdrantClient = Depends(get_qdrant_client)):
            ...
    """
    global _qdrant_client
    
    if _qdrant_client is None:
        try:
            _qdrant_client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                timeout=60,
            )
            
            # Ensure collection exists
            collections = _qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if settings.QDRANT_COLLECTION_NAME not in collection_names:
                logger.info(f"Creating Qdrant collection: {settings.QDRANT_COLLECTION_NAME}")
                _qdrant_client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE,
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise VectorStoreException(f"Failed to connect to Qdrant: {str(e)}")
    
    return _qdrant_client


# Redis Client (singleton)
_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """
    Get or create Redis client.
    
    Usage:
        @app.get("/cached")
        async def get_cached(redis: aioredis.Redis = Depends(get_redis_client)):
            ...
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await _redis_client.ping()
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise Exception(f"Failed to connect to Redis: {str(e)}")
    
    return _redis_client


async def close_db_connections():
    """Close all database connections on shutdown."""
    global _qdrant_client, _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    
    if _qdrant_client:
        _qdrant_client.close()
        _qdrant_client = None
    
    await engine.dispose()
