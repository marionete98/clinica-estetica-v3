"""Memory storage abstractions for the clinic multi-agent system.

Provides MemoryStore interface and implementations:
- RedisMemoryStore: Production Redis backend
- InMemoryStore: Testing/development in-memory backend
"""

from services.memory.memory_store import MemoryStore
from services.memory.redis_memory_store import RedisMemoryStore, redis_memory_store
from services.memory.in_memory_store import InMemoryStore

__all__ = [
    "MemoryStore",
    "RedisMemoryStore",
    "InMemoryStore",
    "redis_memory_store",
]
