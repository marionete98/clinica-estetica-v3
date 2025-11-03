from __future__ import annotations

import asyncio
import logging
from functools import lru_cache
from typing import Any, Dict, Optional
from uuid import UUID

from config.supabase_client import SupabaseClient, get_supabase_client
from models.database import Contact
from services.memory import MemoryStore, redis_memory_store

from .base import DataRepository, cache_not_found, is_not_found

logger = logging.getLogger(__name__)

CONTACT_CACHE_TTL_SECONDS = 3600
CONTACT_PHONE_CACHE_PREFIX = "contact:phone:"
CONTACT_ID_CACHE_PREFIX = "contact:id:"


class ContactRepository(DataRepository):
    """Repository responsible for contact persistence and caching."""

    def __init__(self, supabase: SupabaseClient, cache: Optional[MemoryStore] = None) -> None:
        super().__init__(cache=cache)
        self.supabase = supabase

    async def initialize(self) -> None:  # pragma: no cover - no-op initialization
        return None

    async def close(self) -> None:  # pragma: no cover - resources managed externally
        return None

    async def _cache_contact_data(
        self, contact_data: Dict[str, Any], ttl: int = CONTACT_CACHE_TTL_SECONDS
    ) -> None:
        if not self.cache:
            return
        phone = contact_data.get("phone")
        contact_id = contact_data.get("id")
        if phone:
            await self.cache.set(
                f"{CONTACT_PHONE_CACHE_PREFIX}{phone}", contact_data, ttl=ttl
            )
        if contact_id:
            await self.cache.set(
                f"{CONTACT_ID_CACHE_PREFIX}{contact_id}", contact_data, ttl=ttl
            )

    async def create_or_update_contact(
        self,
        phone: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        consent: bool = False,
    ) -> Dict[str, Any]:
        existing = await self.get_contact_by_phone(phone)

        if existing:
            update_data: Dict[str, Any] = {}
            if name:
                update_data["name"] = name
            if email:
                update_data["email"] = email
            if consent:
                update_data["consent"] = consent

            if update_data:
                def _update_contact() -> Any:
                    return (
                        self.supabase.client.table("contacts")
                        .update(update_data)
                        .eq("id", str(existing["id"]))
                        .execute()
                    )

                response = await asyncio.to_thread(_update_contact)
                contact_data = response.data[0]
                await self._cache_contact_data(contact_data)
                return contact_data

            await self._cache_contact_data(existing)
            return existing

        contact_payload = {
            "phone": phone,
            "name": name,
            "email": email,
            "consent": consent,
        }

        def _insert_contact() -> Any:
            return (
                self.supabase.client.table("contacts")
                .insert(contact_payload)
                .execute()
            )

        response = await asyncio.to_thread(_insert_contact)
        contact_data = response.data[0]
        await self._cache_contact_data(contact_data)
        return contact_data

    async def get_contact_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        cache_key = f"{CONTACT_PHONE_CACHE_PREFIX}{phone}"
        cached_contact: Optional[Dict[str, Any]] = None
        if self.cache:
            cached_contact = await self.cache.get(cache_key)

        if cached_contact is not None:
            if is_not_found(cached_contact):
                return None
            if isinstance(cached_contact, dict):
                return cached_contact
            logger.warning("contact_cache_deserialize_failed", phone=phone)

        def _fetch_contact() -> Any:
            return (
                self.supabase.client.table("contacts")
                .select("*")
                .eq("phone", phone)
                .execute()
            )

        response = await asyncio.to_thread(_fetch_contact)

        if response.data and len(response.data) > 0:
            contact_data = response.data[0]
            await self._cache_contact_data(contact_data)
            return contact_data

        await cache_not_found(self.cache, cache_key)
        return None

    async def get_contact_by_id(self, contact_id: UUID) -> Optional[Dict[str, Any]]:
        cache_key = f"{CONTACT_ID_CACHE_PREFIX}{contact_id}"
        cached_contact: Optional[Dict[str, Any]] = None
        if self.cache:
            cached_contact = await self.cache.get(cache_key)

        if cached_contact is not None:
            if is_not_found(cached_contact):
                return None
            if isinstance(cached_contact, dict):
                return cached_contact
            logger.warning(
                "contact_cache_deserialize_failed", contact_id=str(contact_id)
            )

        def _fetch_contact_by_id() -> Any:
            return (
                self.supabase.client.table("contacts")
                .select("*")
                .eq("id", str(contact_id))
                .execute()
            )

        response = await asyncio.to_thread(_fetch_contact_by_id)

        if response.data and len(response.data) > 0:
            contact_data = response.data[0]
            await self._cache_contact_data(contact_data)
            return contact_data

        await cache_not_found(self.cache, cache_key)
        return None

    async def update_contact(
        self, contact_id: UUID, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if not updates:
            return await self.get_contact_by_id(contact_id)

        def _update_contact() -> Any:
            return (
                self.supabase.client.table("contacts")
                .update(updates)
                .eq("id", str(contact_id))
                .execute()
            )

        response = await asyncio.to_thread(_update_contact)
        if not response.data:
            return None

        contact_data = response.data[0]
        await self._cache_contact_data(contact_data)
        return contact_data

    async def increment_no_show_count(self, contact_id: UUID) -> Optional[int]:
        contact = await self.get_contact_by_id(contact_id)
        if not contact:
            return None

        current_no_show = contact.get("no_show_count") or 0
        new_count = current_no_show + 1

        def _update_no_show() -> Any:
            return (
                self.supabase.client.table("contacts")
                .update({"no_show_count": new_count})
                .eq("id", str(contact_id))
                .execute()
            )

        await asyncio.to_thread(_update_no_show)

        contact_data = dict(contact)
        contact_data["no_show_count"] = new_count
        await self._cache_contact_data(contact_data)
        return new_count


@lru_cache
def get_contact_repository() -> ContactRepository:
    return ContactRepository(
        supabase=get_supabase_client(),
        cache=redis_memory_store,
    )


async def create_or_update_contact(
    phone: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    consent: bool = False,
) -> Contact:
    data = await get_contact_repository().create_or_update_contact(
        phone=phone,
        name=name,
        email=email,
        consent=consent,
    )
    return Contact(**data)


async def get_contact_by_phone(phone: str) -> Optional[Contact]:
    data = await get_contact_repository().get_contact_by_phone(phone)
    return Contact(**data) if data else None


async def get_contact_by_id(contact_id: UUID) -> Optional[Contact]:
    data = await get_contact_repository().get_contact_by_id(contact_id)
    return Contact(**data) if data else None


async def update_contact(
    contact_id: UUID, updates: Dict[str, Any]
) -> Optional[Contact]:
    data = await get_contact_repository().update_contact(contact_id, updates)
    return Contact(**data) if data else None


async def increment_no_show_count(contact_id: UUID) -> Optional[int]:
    return await get_contact_repository().increment_no_show_count(contact_id)


__all__ = [
    "ContactRepository",
    "get_contact_repository",
    "create_or_update_contact",
    "get_contact_by_phone",
    "get_contact_by_id",
    "update_contact",
    "increment_no_show_count",
]
