"""Unit tests for knowledge base repository."""

from __future__ import annotations

import asyncio

import pytest

from models.repositories.knowledge_base import KnowledgeBaseRepository
from services.memory.in_memory_store import InMemoryStore
from utils.exceptions import RepositoryError

from ._helpers import FakeSupabase


@pytest.fixture
async def repository(fake_supabase: FakeSupabase) -> KnowledgeBaseRepository:
    cache = InMemoryStore()
    repo = KnowledgeBaseRepository(supabase=fake_supabase, cache=cache)
    yield repo
    await cache.close()


@pytest.mark.asyncio
async def test_search_filters_by_keywords(repository: KnowledgeBaseRepository, fake_supabase: FakeSupabase) -> None:
    query = fake_supabase.client.table("knowledge_base")
    query._data = [
        {"id": "1", "keywords": ["depilação", "laser"], "excerpt": "info"},
        {"id": "2", "keywords": ["massagem"], "excerpt": "other"},
    ]

    results = await repository.search("Depilação a laser", top_k=1)

    assert len(results) == 1
    assert results[0]["id"] == "1"
    cached = await repository.cache.get("kb:search:all:depilação a laser")
    assert cached[0]["id"] == "1"


@pytest.mark.asyncio
async def test_get_message_template_uses_cache(repository: KnowledgeBaseRepository, fake_supabase: FakeSupabase) -> None:
    query = fake_supabase.client.table("message_templates")
    query._data = {"name": "faq_template", "content": "Olá"}

    template = await repository.get_message_template("faq_template")

    assert template["content"] == "Olá"
    cached = await repository.cache.get("kb:template:faq_template")
    assert cached["name"] == "faq_template"


@pytest.mark.asyncio
async def test_search_raises_repository_error_on_failure(repository: KnowledgeBaseRepository, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _failing_to_thread(func, *args, **kwargs):  # type: ignore[unused-argument]
        raise RuntimeError("boom")

    monkeypatch.setattr(asyncio, "to_thread", _failing_to_thread)

    with pytest.raises(RepositoryError):
        await repository.search("qualquer coisa")
