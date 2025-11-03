"""Unit tests for session repository logic."""

from __future__ import annotations

from typing import Dict

import pytest

from models.repositories.sessions import SessionRepository

from ._helpers import FakeSupabase


@pytest.fixture
async def repository(fake_supabase: FakeSupabase) -> SessionRepository:
    return SessionRepository(supabase=fake_supabase)


@pytest.mark.asyncio
async def test_create_or_update_session_inserts_when_missing(repository: SessionRepository, fake_supabase: FakeSupabase) -> None:
    payload: Dict[str, str] = {"conversation_id": "conv-1", "summary": "Olá"}

    result = await repository.create_or_update_session(payload)

    assert result["conversation_id"] == "conv-1"
    assert fake_supabase.client.table_calls.count("sessions") >= 1


@pytest.mark.asyncio
async def test_create_or_update_session_updates_existing(repository: SessionRepository, fake_supabase: FakeSupabase) -> None:
    query = fake_supabase.client.table("sessions")
    query._data = {"conversation_id": "conv-1", "summary": "old"}

    result = await repository.create_or_update_session(
        {"conversation_id": "conv-1", "summary": "new"}
    )

    assert result["summary"] == "new"
    assert query.history[-1] == ("update", {"conversation_id": "conv-1", "summary": "new"})


@pytest.mark.asyncio
async def test_get_session_by_conversation_id_returns_dict(repository: SessionRepository, fake_supabase: FakeSupabase) -> None:
    query = fake_supabase.client.table("sessions")
    query._data = {"conversation_id": "conv-2", "automation_paused": True}

    result = await repository.get_session_by_conversation_id("conv-2")

    assert result == query._data
