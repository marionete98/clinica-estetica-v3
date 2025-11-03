"""
In-memory implementation of MemoryStore for testing and development.

This implementation uses a Python dictionary for storage and is NOT persistent.
Use only for testing and development.
"""

import asyncio
import fnmatch
import logging
import time
from typing import Any, Optional, List, Dict
from dataclasses import dataclass

from services.memory.memory_store import MemoryStore


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Internal cache entry with expiration tracking."""
    value: Any
    expires_at: Optional[float] = None

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at


class InMemoryStore(MemoryStore):
    """
    In-memory implementation of MemoryStore for testing.
    
    NOT persistent - data is lost when process exits.
    Thread-safe via asyncio locks.
    
    Usage:
        memory = InMemoryStore()
        await memory.set("key", {"data": "value"}, ttl=60)
        value = await memory.get("key")
    """

    def __init__(self):
        """Initialize in-memory store."""
        self._store: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    def _cleanup_expired(self):
        """Remove expired entries (called before reads)."""
        now = time.time()
        expired_keys = [
            key for key, entry in self._store.items()
            if entry.expires_at and entry.expires_at <= now
        ]
        for key in expired_keys:
            del self._store[key]

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from memory."""
        async with self._lock:
            self._cleanup_expired()
            
            entry = self._store.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._store[key]
                return None
            
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Store value in memory."""
        async with self._lock:
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl
            
            self._store[key] = CacheEntry(value=value, expires_at=expires_at)
            return True

    async def delete(self, key: str) -> bool:
        """Delete value from memory."""
        async with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in memory."""
        async with self._lock:
            self._cleanup_expired()
            return key in self._store and not self._store[key].is_expired()

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        async with self._lock:
            self._cleanup_expired()
            
            matching_keys = [
                key for key in self._store.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            
            for key in matching_keys:
                del self._store[key]
            
            return len(matching_keys)

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Retrieve multiple values at once."""
        async with self._lock:
            self._cleanup_expired()
            
            result = {}
            for key in keys:
                entry = self._store.get(key)
                if entry and not entry.is_expired():
                    result[key] = entry.value
            
            return result

    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Store multiple values at once."""
        async with self._lock:
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl
            
            for key, value in items.items():
                self._store[key] = CacheEntry(value=value, expires_at=expires_at)
            
            return True

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value atomically."""
        async with self._lock:
            entry = self._store.get(key)
            
            if entry is None or entry.is_expired():
                new_value = amount
                self._store[key] = CacheEntry(value=new_value)
                return new_value
            
            if not isinstance(entry.value, int):
                raise ValueError(f"Cannot increment non-integer value for key {key}")
            
            new_value = entry.value + amount
            entry.value = new_value
            return new_value

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining time-to-live for key."""
        async with self._lock:
            entry = self._store.get(key)
            
            if entry is None or entry.is_expired():
                return None
            
            if entry.expires_at is None:
                return None
            
            remaining = entry.expires_at - time.time()
            return max(0, int(remaining))

    async def close(self) -> None:
        """Close store (no-op for in-memory)."""
        async with self._lock:
            self._store.clear()

    def clear(self):
        """Clear all data (testing utility)."""
        self._store.clear()

    def size(self) -> int:
        """Get number of entries (testing utility)."""
        return len(self._store)
