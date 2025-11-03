"""
Contact repository operations with Redis caching support.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional
from uuid import UUID

from config.redis_client import redis_client
from config.supabase_client import supabase_client
from models.database import Contact

from .base import cache_not_found, is_not_found, model_to_dict

logger = logging.getLogger(__name__)

CONTACT_CACHE_TTL_SECONDS = 3600
CONTACT_PHONE_CACHE_PREFIX = "contact:phone:"
CONTACT_ID_CACHE_PREFIX = "contact:id:"


async def _cache_contact_data(
    contact_data: Dict[str, Any], ttl: int = CONTACT_CACHE_TTL_SECONDS
) -> None:
    """Cache contact data by phone and id."""
    phone = contact_data.get("phone")
    if phone:
        await redis_client.set_value(
            f"{CONTACT_PHONE_CACHE_PREFIX}{phone}", contact_data, ttl
        )
    contact_id = contact_data.get("id")
    if contact_id:
        await redis_client.set_value(
            f"{CONTACT_ID_CACHE_PREFIX}{contact_id}", contact_data, ttl
        )


async def create_or_update_contact(
    phone: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    consent: bool = False,
) -> Contact:
    """
    Create a new contact or update existing one by phone number.
    """
    supabase = supabase_client.client

    existing = await get_contact_by_phone(phone)

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
                    supabase.table("contacts")
                    .update(update_data)
                    .eq("id", str(existing.id))
                    .execute()
                )

            response = await asyncio.to_thread(_update_contact)
            contact_data = response.data[0]
            await _cache_contact_data(contact_data)
            return Contact(**contact_data)

        await _cache_contact_data(model_to_dict(existing))
        return existing

    contact_payload = {
        "phone": phone,
        "name": name,
        "email": email,
        "consent": consent,
    }

    def _insert_contact() -> Any:
        return supabase.table("contacts").insert(contact_payload).execute()

    response = await asyncio.to_thread(_insert_contact)
    contact_data = response.data[0]
    await _cache_contact_data(contact_data)
    return Contact(**contact_data)


async def get_contact_by_phone(phone: str) -> Optional[Contact]:
    """
    Retrieve contact by phone number.
    """
    cache_key = f"{CONTACT_PHONE_CACHE_PREFIX}{phone}"

    cached_contact = await redis_client.get_value(cache_key)
    if cached_contact is not None:
        if is_not_found(cached_contact):
            return None
        try:
            return Contact(**cached_contact)
        except Exception:
            logger.warning("contact_cache_deserialize_failed", phone=phone)

    supabase = supabase_client.client

    def _fetch_contact() -> Any:
        return supabase.table("contacts").select("*").eq("phone", phone).execute()

    response = await asyncio.to_thread(_fetch_contact)

    if response.data and len(response.data) > 0:
        contact_data = response.data[0]
        await _cache_contact_data(contact_data)
        return Contact(**contact_data)

    await cache_not_found(cache_key)
    return None


async def get_contact_by_id(contact_id: UUID) -> Optional[Contact]:
    """
    Retrieve contact by ID.
    """
    cache_key = f"{CONTACT_ID_CACHE_PREFIX}{contact_id}"

    cached_contact = await redis_client.get_value(cache_key)
    if cached_contact is not None:
        if is_not_found(cached_contact):
            return None
        try:
            return Contact(**cached_contact)
        except Exception:
            logger.warning(
                "contact_cache_deserialize_failed", contact_id=str(contact_id)
            )

    supabase = supabase_client.client

    def _fetch_contact_by_id() -> Any:
        return (
            supabase.table("contacts").select("*").eq("id", str(contact_id)).execute()
        )

    response = await asyncio.to_thread(_fetch_contact_by_id)

    if response.data and len(response.data) > 0:
        contact_data = response.data[0]
        await _cache_contact_data(contact_data)
        return Contact(**contact_data)

    await cache_not_found(cache_key)
    return None


async def increment_no_show_count(contact_id: UUID) -> None:
    """
    Increment no-show count for a contact.
    """
    supabase = supabase_client.client

    contact = await get_contact_by_id(contact_id)
    if contact:
        current_no_show = getattr(contact, "no_show_count", 0) or 0
        new_count = current_no_show + 1

        def _update_no_show() -> Any:
            return (
                supabase.table("contacts")
                .update({"no_show_count": new_count})
                .eq("id", str(contact_id))
                .execute()
            )

        await asyncio.to_thread(_update_no_show)

        contact_data = model_to_dict(contact)
        contact_data["no_show_count"] = new_count
        await _cache_contact_data(contact_data)


__all__ = [
    "create_or_update_contact",
    "get_contact_by_phone",
    "get_contact_by_id",
    "increment_no_show_count",
]
