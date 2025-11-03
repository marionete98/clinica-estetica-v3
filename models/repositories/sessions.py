"""
Conversation session repository operations.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from config.supabase_client import supabase_client
from models.database import Session


async def create_or_update_session(
    conversation_id: str,
    contact_id: Optional[UUID] = None,
    summary: Optional[str] = None,
    last_intent: Optional[str] = None,
    automation_paused: bool = False,
) -> Session:
    """
    Create or update a conversation session.
    """
    supabase = supabase_client.client

    response = (
        supabase.table("sessions")
        .select("*")
        .eq("conversation_id", conversation_id)
        .execute()
    )

    session_payload = {
        "conversation_id": conversation_id,
        "contact_id": str(contact_id) if contact_id else None,
        "summary": summary,
        "last_intent": last_intent,
        "automation_paused": automation_paused,
    }

    if response.data and len(response.data) > 0:
        response = (
            supabase.table("sessions")
            .update(session_payload)
            .eq("conversation_id", conversation_id)
            .execute()
        )
    else:
        response = supabase.table("sessions").insert(session_payload).execute()

    return Session(**response.data[0])


async def get_session_by_conversation_id(conversation_id: str) -> Optional[Session]:
    """
    Retrieve session by conversation ID.
    """
    supabase = supabase_client.client

    response = (
        supabase.table("sessions")
        .select("*")
        .eq("conversation_id", conversation_id)
        .execute()
    )

    if response.data and len(response.data) > 0:
        return Session(**response.data[0])
    return None


__all__ = ["create_or_update_session", "get_session_by_conversation_id"]
