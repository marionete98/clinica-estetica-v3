from __future__ import annotations

from functools import lru_cache

from config.redis_client import RedisClient, get_redis_client as _config_get_redis
from config.supabase_client import (
    SupabaseClient,
    SupabaseOperations,
    get_supabase_client as _config_get_supabase_client,
    get_supabase_operations as _config_get_supabase_operations,
)
from services.embedding_service import EmbeddingService, create_embedding_service
from services.kb_cache_service import KnowledgeBaseCacheService


@lru_cache
def get_redis_client() -> RedisClient:
    """Return shared Redis client instance for dependency injection."""
    return _config_get_redis()


@lru_cache
def get_supabase_client() -> SupabaseClient:
    """Return shared Supabase client instance for dependency injection."""
    return _config_get_supabase_client()


@lru_cache
def get_supabase_ops() -> SupabaseOperations:
    """Return cached Supabase operations helper."""
    return _config_get_supabase_operations()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return create_embedding_service()


@lru_cache
def get_kb_cache_service() -> KnowledgeBaseCacheService:
    return KnowledgeBaseCacheService(
        redis_client=get_redis_client(),
        supabase_client=get_supabase_client(),
        embedding_service=get_embedding_service(),
    )


__all__ = [
    "get_redis_client",
    "get_supabase_client",
    "get_supabase_ops",
    "get_embedding_service",
    "get_kb_cache_service",
]
