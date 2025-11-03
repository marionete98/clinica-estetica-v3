"""
Dependency container helpers centralizando instâncias compartilhadas.
"""

from __future__ import annotations

from functools import lru_cache

from config.redis_client import RedisClient, create_redis_client
from config.supabase_client import (
    SupabaseClient,
    SupabaseOperations,
    create_supabase_client,
    create_supabase_operations,
)
from services.embedding_service import EmbeddingService, create_embedding_service
from services.kb_cache_service import KnowledgeBaseCacheService


@lru_cache
def get_redis_client() -> RedisClient:
    return create_redis_client()


@lru_cache
def get_supabase_client() -> SupabaseClient:
    return create_supabase_client()


@lru_cache
def get_supabase_ops() -> SupabaseOperations:
    return create_supabase_operations(get_supabase_client())


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
