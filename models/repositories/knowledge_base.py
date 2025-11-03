from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any, Dict, List, Optional

from config.supabase_client import SupabaseClient, get_supabase_client
from models.database import KnowledgeBase, MessageTemplate
from services.memory import MemoryStore, redis_memory_store
from utils.exceptions import RepositoryError

from .base import DataRepository, cache_not_found, is_not_found

KB_CACHE_TTL_SECONDS = 1800
KB_RESULT_CACHE_PREFIX = "kb:search:"
KB_TEMPLATE_CACHE_PREFIX = "kb:template:"


class KnowledgeBaseRepository(DataRepository):
    """Repository handling knowledge base queries and template retrieval."""

    def __init__(self, supabase: SupabaseClient, cache: Optional[MemoryStore] = None) -> None:
        super().__init__(cache=cache)
        self.supabase = supabase

    async def initialize(self) -> None:  # pragma: no cover
        return None

    async def close(self) -> None:  # pragma: no cover
        return None

    async def search(
        self, query: str, top_k: int = 5, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        cache_key = f"{KB_RESULT_CACHE_PREFIX}{category or 'all'}:{query.lower()}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                if is_not_found(cached):
                    return []
                if isinstance(cached, list):
                    return cached[:top_k]

        def _fetch() -> Any:
            supabase_query = (
                self.supabase.client.table("knowledge_base")
                .select("*")
                .eq("active", True)
            )
            if category:
                supabase_query = supabase_query.eq("category", category)
            return supabase_query.execute()

        try:
            response = await asyncio.to_thread(_fetch)
        except Exception as exc:
            raise RepositoryError("Failed to search knowledge base") from exc
        results: List[Dict[str, Any]] = []
        lowered = query.lower()
        for item in response.data or []:
            keywords = item.get("keywords") or []
            if any(lowered in (kw or "").lower() for kw in keywords):
                results.append(item)
                if len(results) >= top_k:
                    break

        if self.cache:
            if results:
                await self.cache.set(cache_key, results, ttl=KB_CACHE_TTL_SECONDS)
            else:
                await cache_not_found(self.cache, cache_key)
        return results

    async def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        def _fetch() -> Any:
            return (
                self.supabase.client.table("knowledge_base")
                .select("*")
                .eq("id", entry_id)
                .execute()
            )

        try:
            response = await asyncio.to_thread(_fetch)
        except Exception as exc:
            raise RepositoryError("Failed to load knowledge base entry") from exc
        if response.data:
            return response.data[0]
        return None

    async def get_categories(self) -> List[str]:
        def _fetch() -> Any:
            return (
                self.supabase.client.table("knowledge_base")
                .select("category")
                .eq("active", True)
                .execute()
            )

        try:
            response = await asyncio.to_thread(_fetch)
        except Exception as exc:
            raise RepositoryError("Failed to list knowledge base categories") from exc
        categories = {
            item.get("category")
            for item in response.data or []
            if item.get("category")
        }
        return sorted(categories)

    async def get_message_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        cache_key = f"{KB_TEMPLATE_CACHE_PREFIX}{template_name}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                if is_not_found(cached):
                    return None
                if isinstance(cached, dict):
                    return cached

        def _fetch() -> Any:
            return (
                self.supabase.client.table("message_templates")
                .select("*")
                .eq("name", template_name)
                .eq("active", True)
                .execute()
            )

        try:
            response = await asyncio.to_thread(_fetch)
        except Exception as exc:
            raise RepositoryError("Failed to fetch template") from exc
        if response.data:
            template = response.data[0]
            if self.cache:
                await self.cache.set(cache_key, template, ttl=KB_CACHE_TTL_SECONDS)
            return template

        await cache_not_found(self.cache, cache_key)
        return None


@lru_cache
def get_knowledge_base_repository() -> KnowledgeBaseRepository:
    return KnowledgeBaseRepository(
        supabase=get_supabase_client(),
        cache=redis_memory_store,
    )


async def search_knowledge_base(
    keywords: List[str], category: Optional[str] = None
) -> List[KnowledgeBase]:
    query = " ".join(keywords)
    results = await get_knowledge_base_repository().search(query, category=category)
    return [KnowledgeBase(**item) for item in results]


async def get_message_template(name: str) -> Optional[MessageTemplate]:
    data = await get_knowledge_base_repository().get_message_template(name)
    return MessageTemplate(**data) if data else None


__all__ = [
    "KnowledgeBaseRepository",
    "get_knowledge_base_repository",
    "search_knowledge_base",
    "get_message_template",
]
