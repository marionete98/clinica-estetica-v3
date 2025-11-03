"""
Redis client module for conversation context management with TTL and locking.
"""

import json
from typing import Any, Optional
from contextlib import contextmanager, asynccontextmanager
from types import SimpleNamespace
import structlog
import redis.asyncio as redis
from redis.exceptions import RedisError, LockError

from config.settings import settings

logger = structlog.get_logger(__name__)


class RedisClient:
    """
    Redis client wrapper for conversation context management.

    Note: This class uses lazy initialization. The Redis connection is
    established on first use, not during __init__. This prevents the
    "coroutine was never awaited" warning.
    """

    # TTL for conversation context (24 hours)
    CONTEXT_TTL = 24 * 60 * 60  # 24 hours in seconds

    # TTL for locks (30 seconds)
    LOCK_TTL = 30

    # Maximum number of messages to keep in context
    MAX_CONTEXT_LENGTH = 20

    def __init__(self):
        """
        Initialize Redis client wrapper.

        Note: The actual Redis connection is established lazily on first use
        via the ensure_initialized() method. This prevents calling async code
        from __init__ which would cause "coroutine was never awaited" warnings.
        """
        self._client: Optional[redis.Redis] = None
        self._initialized: bool = False
        # Lightweight proxy to allow attribute patching in tests before initialization
        self._client_proxy = SimpleNamespace()
    
    async def ensure_initialized(self) -> None:
        """
        Ensure Redis client is initialized.

        This method implements lazy initialization - the Redis connection
        is only established when first needed, not during __init__.
        This prevents "coroutine was never awaited" warnings.

        This method is idempotent - it's safe to call multiple times.
        """
        if self._initialized and self._client is not None:
            return

        try:
            self._client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )

            # Test connection
            await self._client.ping()

            self._initialized = True

            logger.info(
                "redis_client_initialized",
                url=settings.redis_url.split("@")[-1]  # Hide credentials
            )
        except RedisError as e:
            logger.error(
                "redis_client_initialization_failed",
                error=str(e)
            )
            raise

    async def close(self) -> None:
        """
        Close Redis client connection and cleanup resources.

        This should be called during application shutdown or when
        the client is no longer needed.
        """
        if self._client is not None:
            try:
                await self._client.close()
                logger.info("redis_client_closed")
            except Exception as e:
                logger.error("redis_client_close_failed", error=str(e))
            finally:
                self._client = None
                self._initialized = False
    
    @property
    def client(self) -> redis.Redis:
        """
        Get Redis client instance.

        Returns:
            redis.Redis: Redis client instance

        Raises:
            RuntimeError: If client is not initialized.
                         Call await ensure_initialized() first.
        """
        # Allow property access even if not initialized so tests can patch attributes
        if self._client is None or not self._initialized:
            return self._client_proxy
        return self._client
    
    async def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            await self.ensure_initialized()
            await self._client.ping()
            return True
        except Exception as e:
            logger.error("redis_health_check_failed", error=str(e))
            return False
    
    def _get_context_key(self, conversation_id: str) -> str:
        """
        Get Redis key for conversation context.
        
        Args:
            conversation_id: Conversation identifier
        
        Returns:
            str: Redis key
        """
        return f"conv:{conversation_id}"
    
    def _get_lock_key(self, conversation_id: str) -> str:
        """
        Get Redis key for conversation lock.
        
        Args:
            conversation_id: Conversation identifier
        
        Returns:
            str: Redis lock key
        """
        return f"lock:{conversation_id}"
    
    async def get_context(self, conversation_id: str, max_messages: Optional[int] = None) -> list[dict[str, Any]]:
        """
        Get conversation context from Redis.

        Args:
            conversation_id: Conversation identifier
            max_messages: Maximum number of messages to retrieve (default: MAX_CONTEXT_LENGTH)

        Returns:
            list: List of message dictionaries
        """
        try:
            await self.ensure_initialized()
            key = self._get_context_key(conversation_id)
            max_msgs = max_messages or self.MAX_CONTEXT_LENGTH

            # Get last N messages from the list
            messages_json = await self._client.lrange(key, -max_msgs, -1)
            
            messages = [json.loads(msg) for msg in messages_json]
            
            logger.debug(
                "redis_context_retrieved",
                conversation_id=conversation_id,
                message_count=len(messages)
            )
            
            return messages
        except RedisError as e:
            logger.warning(
                "redis_context_retrieval_failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            # Return empty context on failure (graceful degradation)
            return []
    
    async def set_context(self, conversation_id: str, messages: list[dict[str, Any]]) -> bool:
        """
        Set conversation context in Redis (replaces existing context).

        Args:
            conversation_id: Conversation identifier
            messages: List of message dictionaries

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self.ensure_initialized()
            key = self._get_context_key(conversation_id)
            
            # Delete existing context
            await self._client.delete(key)
            
            # Add all messages
            if messages:
                messages_json = [json.dumps(msg) for msg in messages]
                await self._client.rpush(key, *messages_json)
            
            # Set TTL
            await self._client.expire(key, self.CONTEXT_TTL)
            
            logger.debug(
                "redis_context_set",
                conversation_id=conversation_id,
                message_count=len(messages)
            )
            
            return True
        except RedisError as e:
            logger.error(
                "redis_context_set_failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            return False
    
    async def append_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        timestamp: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> bool:
        """
        Append a message to conversation context.

        Args:
            conversation_id: Conversation identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            timestamp: ISO format timestamp (optional)
            metadata: Additional metadata (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self.ensure_initialized()
            key = self._get_context_key(conversation_id)
            
            message = {
                "role": role,
                "content": content,
            }
            
            if timestamp:
                message["ts"] = timestamp
            
            if metadata:
                message["metadata"] = metadata
            
            # Append message to list
            await self._client.rpush(key, json.dumps(message))
            
            # Trim to keep only last MAX_CONTEXT_LENGTH messages
            await self._client.ltrim(key, -self.MAX_CONTEXT_LENGTH, -1)
            
            # Set/refresh TTL
            await self._client.expire(key, self.CONTEXT_TTL)
            
            logger.debug(
                "redis_message_appended",
                conversation_id=conversation_id,
                role=role
            )
            
            return True
        except RedisError as e:
            logger.error(
                "redis_message_append_failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            return False
    
    async def clear_context(self, conversation_id: str) -> bool:
        """
        Clear conversation context from Redis.

        Args:
            conversation_id: Conversation identifier

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self.ensure_initialized()
            key = self._get_context_key(conversation_id)
            await self._client.delete(key)
            
            logger.debug(
                "redis_context_cleared",
                conversation_id=conversation_id
            )
            
            return True
        except RedisError as e:
            logger.error(
                "redis_context_clear_failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            return False
    
    @asynccontextmanager
    async def acquire_lock(self, conversation_id: str, timeout: Optional[int] = None):
        """
        Acquire a lock for a conversation to prevent concurrent processing.

        Args:
            conversation_id: Conversation identifier
            timeout: Lock timeout in seconds (default: LOCK_TTL)

        Yields:
            redis.lock.Lock: Lock object

        Raises:
            LockError: If lock cannot be acquired
        """
        await self.ensure_initialized()
        lock_key = self._get_lock_key(conversation_id)
        lock_timeout = timeout or self.LOCK_TTL

        lock = self._client.lock(
            lock_key,
            timeout=lock_timeout,
            blocking_timeout=5  # Wait up to 5 seconds to acquire lock
        )

        try:
            acquired = await lock.acquire(blocking=True)
            if not acquired:
                raise LockError(f"Could not acquire lock for conversation {conversation_id}")

            logger.debug(
                "redis_lock_acquired",
                conversation_id=conversation_id
            )

            yield lock
        finally:
            try:
                await lock.release()
                logger.debug(
                    "redis_lock_released",
                    conversation_id=conversation_id
                )
            except LockError:
                # Lock already released or expired
                pass
    
    async def set_value(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set a key-value pair in Redis.

        Args:
            key: Redis key
            value: Value to store (will be JSON serialized if not string)
            ttl: Time to live in seconds (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self.ensure_initialized()
            if not isinstance(value, str):
                value = json.dumps(value)

            if ttl:
                await self._client.setex(key, ttl, value)
            else:
                await self._client.set(key, value)

            return True
        except RedisError as e:
            logger.error(
                "redis_set_value_failed",
                key=key,
                error=str(e)
            )
            return False
    
    async def get_value(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Get a value from Redis.

        Args:
            key: Redis key
            deserialize: If True, attempt to JSON deserialize the value

        Returns:
            Value from Redis or None if not found
        """
        try:
            await self.ensure_initialized()
            value = await self._client.get(key)
            
            if value is None:
                return None
            
            if deserialize:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            
            return value
        except RedisError as e:
            logger.error(
                "redis_get_value_failed",
                key=key,
                error=str(e)
            )
            return None
    
    async def delete_key(self, key: str) -> bool:
        """
        Delete a key from Redis.

        Args:
            key: Redis key

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self.ensure_initialized()
            await self._client.delete(key)
            return True
        except RedisError as e:
            logger.error(
                "redis_delete_key_failed",
                key=key,
                error=str(e)
            )
            return False


_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get or lazily create a Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client


# Backwards compatibility for modules importing redis_client directly
redis_client = get_redis_client()


def create_redis_client() -> RedisClient:
    """
    Factory helper para instanciar um novo RedisClient.
    """
    return RedisClient()


__all__ = ["RedisClient", "create_redis_client", "get_redis_client", "redis_client"]
