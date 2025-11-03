"""
Service repository operations with Redis caching.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, List, Optional
from uuid import UUID

from config.redis_client import redis_client
from config.supabase_client import supabase_client
from models.database import Service

from .base import cache_not_found, is_not_found

logger = logging.getLogger(__name__)

SERVICE_CACHE_TTL_SECONDS = 3600
SERVICE_CACHE_PREFIX = "service:id:"
SERVICE_LIST_CACHE_PREFIX = "service:list:"


async def _cache_service_data(
    service_data: dict, ttl: int = SERVICE_CACHE_TTL_SECONDS
) -> None:
    """Cache service details by id."""
    service_id = service_data.get("id")
    if service_id:
        await redis_client.set_value(
            f"{SERVICE_CACHE_PREFIX}{service_id}", service_data, ttl
        )


async def get_service_by_id(service_id: UUID) -> Optional[Service]:
    """
    Retrieve service by ID.
    """
    cache_key = f"{SERVICE_CACHE_PREFIX}{service_id}"

    cached_service = await redis_client.get_value(cache_key)
    if cached_service is not None:
        if is_not_found(cached_service):
            return None
        try:
            return Service(**cached_service)
        except Exception:
            logger.warning(
                "service_cache_deserialize_failed", service_id=str(service_id)
            )

    supabase = supabase_client.client

    def _fetch_service() -> Any:
        return (
            supabase.table("services").select("*").eq("id", str(service_id)).execute()
        )

    response = await asyncio.to_thread(_fetch_service)

    if response.data and len(response.data) > 0:
        service_data = response.data[0]
        await _cache_service_data(service_data)
        return Service(**service_data)

    await cache_not_found(cache_key)
    return None


async def list_active_services(category: Optional[str] = None) -> List[Service]:
    """
    List all active services, optionally filtered by category.
    """
    cache_key_suffix = category or "all"
    cache_key = f"{SERVICE_LIST_CACHE_PREFIX}{cache_key_suffix}"

    cached_services = await redis_client.get_value(cache_key)
    if cached_services is not None:
        return [Service(**svc) for svc in cached_services]

    supabase = supabase_client.client

    def _fetch_services() -> Any:
        query = supabase.table("services").select("*").eq("active", True)
        if category:
            query = query.eq("category", category)
        return query.order("name").execute()

    response = await asyncio.to_thread(_fetch_services)
    services_data = response.data or []

    if services_data:
        await redis_client.set_value(
            cache_key, services_data, SERVICE_CACHE_TTL_SECONDS
        )
        for service in services_data:
            await _cache_service_data(service)
        return [Service(**svc) for svc in services_data]

    await redis_client.set_value(cache_key, [], SERVICE_CACHE_TTL_SECONDS)
    return []


__all__ = ["get_service_by_id", "list_active_services"]
