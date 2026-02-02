"""
Redis Cache Service for RAG Application

Provides caching for:
- Query embeddings
- Search results
- Document metadata
- Conversation history
"""

import json
import hashlib
from typing import Optional, List, Any, Dict
from redis import asyncio as aioredis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service with async support"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.default_ttl = 3600  # 1 hour
        self.embedding_ttl = 86400  # 24 hours
        self.query_ttl = 1800  # 30 minutes
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5
            )
            await self.redis.ping()
            logger.info("✅ Connected to Redis cache")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    def _generate_key(self, prefix: str, data: str) -> str:
        """Generate cache key using hash"""
        hash_obj = hashlib.sha256(data.encode())
        return f"{prefix}:{hash_obj.hexdigest()[:16]}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache GET error for {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.redis:
            return False
        
        try:
            serialized = json.dumps(value)
            ttl = ttl or self.default_ttl
            await self.redis.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache SET error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache DELETE error for {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.redis:
            return 0
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache CLEAR error for pattern {pattern}: {e}")
            return 0
    
    # ==================== Embedding Cache ====================
    
    async def get_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """Get cached embedding for text"""
        key = self._generate_key(f"emb:{model}", text)
        return await self.get(key)
    
    async def set_embedding(self, text: str, model: str, embedding: List[float]) -> bool:
        """Cache embedding for text"""
        key = self._generate_key(f"emb:{model}", text)
        return await self.set(key, embedding, self.embedding_ttl)
    
    # ==================== Query Cache ====================
    
    async def get_query_result(self, query: str, top_k: int, use_hybrid: bool) -> Optional[Dict]:
        """Get cached query results"""
        cache_key = f"{query}|k={top_k}|hybrid={use_hybrid}"
        key = self._generate_key("query", cache_key)
        return await self.get(key)
    
    async def set_query_result(
        self, 
        query: str, 
        top_k: int, 
        use_hybrid: bool, 
        results: Dict
    ) -> bool:
        """Cache query results"""
        cache_key = f"{query}|k={top_k}|hybrid={use_hybrid}"
        key = self._generate_key("query", cache_key)
        return await self.set(key, results, self.query_ttl)
    
    # ==================== Document Cache ====================
    
    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get cached document metadata"""
        key = f"doc:{doc_id}"
        return await self.get(key)
    
    async def set_document(self, doc_id: str, doc_data: Dict) -> bool:
        """Cache document metadata"""
        key = f"doc:{doc_id}"
        return await self.set(key, doc_data, self.default_ttl)
    
    async def invalidate_document(self, doc_id: str) -> bool:
        """Invalidate document cache"""
        return await self.delete(f"doc:{doc_id}")
    
    # ==================== Conversation Cache ====================
    
    async def get_conversation(self, conv_id: str) -> Optional[Dict]:
        """Get cached conversation"""
        key = f"conv:{conv_id}"
        return await self.get(key)
    
    async def set_conversation(self, conv_id: str, conv_data: Dict) -> bool:
        """Cache conversation"""
        key = f"conv:{conv_id}"
        return await self.set(key, conv_data, ttl=1800)  # 30 min
    
    # ==================== Statistics ====================
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis:
            return {"connected": False}
        
        try:
            info = await self.redis.info("stats")
            memory = await self.redis.info("memory")
            
            return {
                "connected": True,
                "total_keys": await self.redis.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "memory_used": memory.get("used_memory_human", "N/A"),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"connected": False, "error": str(e)}
    
    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> str:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return "0.00%"
        return f"{(hits / total * 100):.2f}%"


# Global cache instance
cache_service = CacheService()


async def get_cache() -> CacheService:
    """Dependency injection for cache service"""
    if not cache_service.redis:
        await cache_service.connect()
    return cache_service
