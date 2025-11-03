"""
Shared utilities for repository modules.
"""

from __future__ import annotations

from typing import Any, Dict

from config.redis_client import redis_client

NOT_FOUND_TTL_SECONDS = 300
_NOT_FOUND_SENTINEL = {"__not_found__": True}


def model_to_dict(model: Any) -> Dict[str, Any]:
    """Convert a Pydantic model or dict-like object to dict."""
    if isinstance(model, dict):
        return model
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model)


def is_not_found(value: Any) -> bool:
    """Check if cached value matches the not-found sentinel."""
    return isinstance(value, dict) and value.get("__not_found__") is True


async def cache_not_found(key: str, ttl: int = NOT_FOUND_TTL_SECONDS) -> None:
    """Cache sentinel value for missed lookups to avoid repeated queries."""
    await redis_client.set_value(key, _NOT_FOUND_SENTINEL, ttl)


__all__ = ["NOT_FOUND_TTL_SECONDS", "model_to_dict", "is_not_found", "cache_not_found"]
