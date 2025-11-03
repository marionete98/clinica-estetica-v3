"""Unit tests for message template repository."""

from __future__ import annotations

import pytest

from models.repositories.template_repository import TemplateRepository
from services.memory.in_memory_store import InMemoryStore

from ._helpers import FakeSupabase


@pytest.fixture
async def repository(fake_supabase: FakeSupabase) -> TemplateRepository:
    cache = InMemoryStore()
    repo = TemplateRepository(supabase=fake_supabase, cache=cache)
    yield repo
    await cache.close()


@pytest.mark.asyncio
async def test_get_message_template_caches_results(repository: TemplateRepository, fake_supabase: FakeSupabase) -> None:
    query = fake_supabase.client.table("message_templates")
    query._data = {"name": "faq_greeting", "content": "Olá, {name}!"}

    template = await repository.get_message_template("faq_greeting")

    assert template["content"] == "Olá, {name}!"
    cached = await repository.cache.get("template:name:faq_greeting")
    assert cached["name"] == "faq_greeting"


@pytest.mark.asyncio
async def test_list_templates_returns_cached_list(repository: TemplateRepository, fake_supabase: FakeSupabase) -> None:
    query = fake_supabase.client.table("message_templates")
    query._data = [
        {"name": "one", "content": "..."},
        {"name": "two", "content": "..."},
    ]

    templates = await repository.list_templates()

    assert len(templates) == 2
    cached = await repository.cache.get("template:list:all")
    assert len(cached) == 2


@pytest.mark.asyncio
async def test_format_template_applies_variables(repository: TemplateRepository, fake_supabase: FakeSupabase) -> None:
    query = fake_supabase.client.table("message_templates")
    query._data = {"name": "farewell", "content": "Até logo, ${name}!"}

    formatted = await repository.format_template("farewell", {"name": "Luana"})

    assert formatted == "Até logo, Luana!"
