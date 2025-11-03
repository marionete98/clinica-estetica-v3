from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any, Dict, Optional
from uuid import UUID

from config.supabase_client import SupabaseClient, get_supabase_client
from models.database import Session

from .base import DataRepository


class SessionRepository(DataRepository):
    """Repository for managing conversation session state."""

    def __init__(self, supabase: SupabaseClient) -> None:
        super().__init__(cache=None)
        self.supabase = supabase

    async def initialize(self) -> None:  # pragma: no cover
        return None

    async def close(self) -> None:  # pragma: no cover
        return None

    async def create_or_update_session(
        self,
        session_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        conversation_id = session_data["conversation_id"]

        def _select() -> Any:
            return (
                self.supabase.client.table("sessions")
                .select("*")
                .eq("conversation_id", conversation_id)
                .execute()
            )

        existing = await asyncio.to_thread(_select)

        def _write() -> Any:
            query = self.supabase.client.table("sessions")
            if existing.data:
                return query.update(session_data).eq("conversation_id", conversation_id).execute()
            return query.insert(session_data).execute()

        response = await asyncio.to_thread(_write)
        return response.data[0]

    async def get_session_by_conversation_id(
        self, conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        def _fetch() -> Any:
            return (
                self.supabase.client.table("sessions")
                .select("*")
                .eq("conversation_id", conversation_id)
                .execute()
            )

        response = await asyncio.to_thread(_fetch)
        if response.data:
            return response.data[0]
        return None


@lru_cache
def get_session_repository() -> SessionRepository:
    return SessionRepository(supabase=get_supabase_client())


async def create_or_update_session(
    conversation_id: str,
    contact_id: Optional[UUID] = None,
    summary: Optional[str] = None,
    last_intent: Optional[str] = None,
    automation_paused: bool = False,
) -> Session:
    payload: Dict[str, Any] = {
        "conversation_id": conversation_id,
        "contact_id": str(contact_id) if contact_id else None,
        "summary": summary,
        "last_intent": last_intent,
        "automation_paused": automation_paused,
    }
    data = await get_session_repository().create_or_update_session(payload)
    return Session(**data)


async def get_session_by_conversation_id(conversation_id: str) -> Optional[Session]:
    data = await get_session_repository().get_session_by_conversation_id(conversation_id)
    return Session(**data) if data else None


__all__ = [
    "SessionRepository",
    "get_session_repository",
    "create_or_update_session",
    "get_session_by_conversation_id",
]
