"""Memory Store abstract interface for the clinic multi-agent system.

Provides abstraction over caching/memory backends to decouple business logic
from specific implementations like Redis.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict


class MemoryStore(ABC):
    """
    Abstract base class for memory/cache storage.
    
    This interface allows agents to store and retrieve conversation context,
    cache results, and manage temporary data without coupling to specific
    storage backends.
    
    Implementations:
        - RedisMemoryStore: Production Redis backend
        - InMemoryStore: Testing/development in-memory backend
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from memory store.
        
        Args:
            key: Storage key
            
        Returns:
            Value if exists, None otherwise
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store value in memory store.
        
        Args:
            key: Storage key
            value: Value to store (will be serialized)
            ttl: Time-to-live in seconds (None = no expiration)
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete value from memory store.
        
        Args:
            key: Storage key
            
        Returns:
            True if key existed and was deleted, False otherwise
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in memory store.
        
        Args:
            key: Storage key
            
        Returns:
            True if key exists, False otherwise
        """
        pass

    @abstractmethod
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "conversation:*")
            
        Returns:
            Number of keys deleted
        """
        pass

    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Retrieve multiple values at once.
        
        Args:
            keys: List of storage keys
            
        Returns:
            Dictionary mapping keys to values (missing keys omitted)
        """
        pass

    @abstractmethod
    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store multiple values at once.
        
        Args:
            items: Dictionary mapping keys to values
            ttl: Time-to-live in seconds for all items
            
        Returns:
            True if all successful, False otherwise
        """
        pass

    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment numeric value atomically.
        
        Args:
            key: Storage key
            amount: Amount to increment (can be negative)
            
        Returns:
            New value after increment
        """
        pass

    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining time-to-live for key.
        
        Args:
            key: Storage key
            
        Returns:
            Remaining TTL in seconds, None if key doesn't exist or has no expiration
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close connection and cleanup resources.
        """
        pass

    async def get_or_set(
        self,
        key: str,
        factory: callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or compute and store it.
        
        Args:
            key: Storage key
            factory: Async callable that computes value if not cached
            ttl: Time-to-live in seconds
            
        Returns:
            Cached or computed value
        """
        value = await self.get(key)
        if value is not None:
            return value
        
        value = await factory()
        await self.set(key, value, ttl=ttl)
        return value
