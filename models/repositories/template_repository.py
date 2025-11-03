from __future__ import annotations

import asyncio
from functools import lru_cache
from string import Template
from typing import Any, Dict, List, Optional

from config.supabase_client import SupabaseClient, get_supabase_client
from services.memory import MemoryStore, redis_memory_store

from .base import DataRepository, cache_not_found, is_not_found

TEMPLATE_CACHE_PREFIX = "template:name:"
TEMPLATE_LIST_CACHE_PREFIX = "template:list:"
TEMPLATE_CACHE_TTL_SECONDS = 1800


class TemplateRepository(DataRepository):
    """Repository for retrieving and formatting message templates."""

    def __init__(self, supabase: SupabaseClient, cache: Optional[MemoryStore] = None) -> None:
        super().__init__(cache=cache)
        self.supabase = supabase

    async def initialize(self) -> None:  # pragma: no cover
        return None

    async def close(self) -> None:  # pragma: no cover
        return None

    async def get_message_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        cache_key = f"{TEMPLATE_CACHE_PREFIX}{template_name}"
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

        response = await asyncio.to_thread(_fetch)
        if response.data:
            template = response.data[0]
            if self.cache:
                await self.cache.set(cache_key, template, ttl=TEMPLATE_CACHE_TTL_SECONDS)
            return template

        await cache_not_found(self.cache, cache_key)
        return None

    async def list_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        cache_key = f"{TEMPLATE_LIST_CACHE_PREFIX}{category or 'all'}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if isinstance(cached, list):
                return cached

        def _fetch() -> Any:
            query = (
                self.supabase.client.table("message_templates")
                .select("*")
                .eq("active", True)
            )
            if category:
                query = query.eq("category", category)
            return query.order("name").execute()

        response = await asyncio.to_thread(_fetch)
        templates = response.data or []
        if self.cache:
            await self.cache.set(cache_key, templates, ttl=TEMPLATE_CACHE_TTL_SECONDS)
        return templates

    async def format_template(
        self, template_name: str, variables: Dict[str, Any]
    ) -> Optional[str]:
        template = await self.get_message_template(template_name)
        if not template:
            return None
        content = template.get("content") or ""
        try:
            return Template(content).safe_substitute(variables)
        except Exception:
            return content


@lru_cache
def get_template_repository() -> TemplateRepository:
    return TemplateRepository(
        supabase=get_supabase_client(),
        cache=redis_memory_store,
    )


__all__ = [
    "TemplateRepository",
    "get_template_repository",
]
