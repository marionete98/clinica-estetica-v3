"""Unit tests for service repository operations."""

from __future__ import annotations

import pytest
from uuid import UUID

from models.repositories.services import ServiceRepository
from services.memory.in_memory_store import InMemoryStore

from ._helpers import FakeSupabase


@pytest.fixture
async def repository(fake_supabase: FakeSupabase) -> ServiceRepository:
    cache = InMemoryStore()
    repo = ServiceRepository(supabase=fake_supabase, cache=cache)
    yield repo
    await cache.close()


@pytest.mark.asyncio
async def test_get_service_by_id_returns_cached_value(repository: ServiceRepository) -> None:
    service_id = UUID("12345678-1234-5678-1234-567812345678")
    await repository.cache.set(
        f"service:id:{service_id}", {"id": str(service_id), "name": "Laser"}
    )

    result = await repository.get_service_by_id(service_id)

    assert result["name"] == "Laser"


@pytest.mark.asyncio
async def test_list_active_services_populates_cache(repository: ServiceRepository, fake_supabase: FakeSupabase) -> None:
    query = fake_supabase.client.table("services")
    query._data = [
        {"id": "svc-1", "name": "Laser", "active": True},
        {"id": "svc-2", "name": "Peeling", "active": True},
    ]

    services = await repository.list_active_services()

    assert len(services) == 2
    cached = await repository.cache.get("service:list:all")
    assert len(cached) == 2
