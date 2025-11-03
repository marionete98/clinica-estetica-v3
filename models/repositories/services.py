from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional
from uuid import UUID

from config.supabase_client import SupabaseClient, get_supabase_client
from models.database import Service
from services.memory import MemoryStore, redis_memory_store

from .base import DataRepository, cache_not_found, is_not_found

logger = logging.getLogger(__name__)

SERVICE_CACHE_TTL_SECONDS = 3600
SERVICE_CACHE_PREFIX = "service:id:"
SERVICE_LIST_CACHE_PREFIX = "service:list:"


class ServiceRepository(DataRepository):
    """Repository encapsulating clinic service lookups."""

    def __init__(self, supabase: SupabaseClient, cache: Optional[MemoryStore] = None) -> None:
        super().__init__(cache=cache)
        self.supabase = supabase

    async def initialize(self) -> None:  # pragma: no cover
        return None

    async def close(self) -> None:  # pragma: no cover
        return None

    async def _cache_service_data(
        self, service_data: Dict[str, Any], ttl: int = SERVICE_CACHE_TTL_SECONDS
    ) -> None:
        if not self.cache:
            return
        service_id = service_data.get("id")
        if service_id:
            await self.cache.set(
                f"{SERVICE_CACHE_PREFIX}{service_id}", service_data, ttl=ttl
            )

    async def get_service_by_id(self, service_id: UUID) -> Optional[Dict[str, Any]]:
        cache_key = f"{SERVICE_CACHE_PREFIX}{service_id}"
        cached_service: Optional[Dict[str, Any]] = None
        if self.cache:
            cached_service = await self.cache.get(cache_key)

        if cached_service is not None:
            if is_not_found(cached_service):
                return None
            if isinstance(cached_service, dict):
                return cached_service
            logger.warning("service_cache_deserialize_failed", service_id=str(service_id))

        def _fetch_service() -> Any:
            return (
                self.supabase.client.table("services")
                .select("*")
                .eq("id", str(service_id))
                .execute()
            )

        response = await asyncio.to_thread(_fetch_service)

        if response.data and len(response.data) > 0:
            service_data = response.data[0]
            await self._cache_service_data(service_data)
            return service_data

        await cache_not_found(self.cache, cache_key)
        return None

    async def list_active_services(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        cache_key_suffix = category or "all"
        cache_key = f"{SERVICE_LIST_CACHE_PREFIX}{cache_key_suffix}"

        if self.cache:
            cached_services = await self.cache.get(cache_key)
            if cached_services is not None:
                if isinstance(cached_services, list):
                    return cached_services

        def _fetch_services() -> Any:
            query = (
                self.supabase.client.table("services")
                .select("*")
                .eq("active", True)
            )
            if category:
                query = query.eq("category", category)
            return query.order("name").execute()

        response = await asyncio.to_thread(_fetch_services)
        services_data = response.data or []

        if self.cache:
            await self.cache.set(cache_key, services_data, ttl=SERVICE_CACHE_TTL_SECONDS)
            for service in services_data:
                await self._cache_service_data(service)

        return services_data


@lru_cache
def get_service_repository() -> ServiceRepository:
    return ServiceRepository(
        supabase=get_supabase_client(),
        cache=redis_memory_store,
    )


async def get_service_by_id(service_id: UUID) -> Optional[Service]:
    data = await get_service_repository().get_service_by_id(service_id)
    return Service(**data) if data else None


async def list_active_services(category: Optional[str] = None) -> List[Service]:
    services = await get_service_repository().list_active_services(category)
    return [Service(**svc) for svc in services]


__all__ = [
    "ServiceRepository",
    "get_service_repository",
    "get_service_by_id",
    "list_active_services",
]
