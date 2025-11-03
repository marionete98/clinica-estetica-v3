"""Common infrastructure for domain-specific repository implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from services.memory import MemoryStore

NOT_FOUND_TTL_SECONDS = 300
_NOT_FOUND_SENTINEL: Dict[str, Any] = {"__not_found__": True}


class DataRepository(ABC):
    """Base contract for data access repositories."""

    def __init__(self, cache: Optional[MemoryStore] = None) -> None:
        self.cache = cache

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize repository connections/resources."""

    @abstractmethod
    async def close(self) -> None:
        """Release underlying resources."""


def model_to_dict(model: Any) -> Dict[str, Any]:
    """Convert a pydantic model or dict-like object into a dictionary."""

    if isinstance(model, dict):
        return dict(model)
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model)


def is_not_found(value: Any) -> bool:
    """Detect cached sentinel values representing not-found lookups."""

    return isinstance(value, dict) and value.get("__not_found__") is True


async def cache_not_found(
    cache: Optional[MemoryStore],
    key: str,
    ttl: int = NOT_FOUND_TTL_SECONDS,
) -> None:
    """Store a not-found sentinel value when lookups miss the backing store."""

    if cache is None:
        return
    await cache.set(key, _NOT_FOUND_SENTINEL, ttl=ttl)


__all__ = [
    "DataRepository",
    "NOT_FOUND_TTL_SECONDS",
    "cache_not_found",
    "is_not_found",
    "model_to_dict",
]
