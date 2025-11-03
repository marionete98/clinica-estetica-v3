"""Redis-backed MemoryStore implementation used in production."""

import json
import logging
from typing import Any, Optional, List, Dict

from services.memory.memory_store import MemoryStore
from config.redis_client import redis_client as _redis_client


logger = logging.getLogger(__name__)


class RedisMemoryStore(MemoryStore):
    """
    Redis-backed implementation of MemoryStore.
    
    Wraps the existing RedisClient to provide the MemoryStore interface,
    enabling dependency injection and easier testing.
    
    Usage:
        memory = RedisMemoryStore()
        await memory.set("key", {"data": "value"}, ttl=3600)
        value = await memory.get("key")
    """

    def __init__(self, redis_client=None):
        """
        Initialize Redis memory store.
        
        Args:
            redis_client: Optional Redis client (uses global client if None)
        """
        self._client = redis_client or _redis_client

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from Redis."""
        try:
            value = await self._client.get(key)
            if value is None:
                return None
            
            if isinstance(value, (dict, list)):
                return value
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Store value in Redis."""
        try:
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            elif isinstance(value, str):
                serialized = value
            else:
                serialized = json.dumps(value)
            
            return await self._client.set(key, serialized, ex=ttl)
            
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from Redis."""
        try:
            result = await self._client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            result = await self._client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        try:
            keys = await self._client.keys(pattern)
            if not keys:
                return 0
            
            deleted = 0
            for key in keys:
                if await self._client.delete(key):
                    deleted += 1
            return deleted
            
        except Exception as e:
            logger.error(f"Redis invalidate_pattern error for {pattern}: {e}")
            return 0

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Retrieve multiple values at once."""
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Store multiple values at once."""
        try:
            for key, value in items.items():
                if not await self.set(key, value, ttl=ttl):
                    return False
            return True
        except Exception as e:
            logger.error(f"Redis set_many error: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value atomically."""
        try:
            return await self._client.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            return 0

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining time-to-live for key."""
        try:
            ttl = await self._client.ttl(key)
            if ttl < 0:
                return None
            return ttl
        except Exception as e:
            logger.error(f"Redis get_ttl error for key {key}: {e}")
            return None

    async def close(self) -> None:
        """Close Redis connection."""
        try:
            await self._client.close()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")


redis_memory_store = RedisMemoryStore()
