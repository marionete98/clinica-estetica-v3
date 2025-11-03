import pytest

from models.repositories.contacts import ContactRepository
from services.memory.in_memory_store import InMemoryStore

from ._helpers import FakeSupabase


@pytest.fixture
async def repository(fake_supabase: FakeSupabase) -> ContactRepository:
    supabase = fake_supabase
    cache = InMemoryStore()

    repo = ContactRepository(supabase=supabase, cache=cache)
    yield repo
    await cache.close()


@pytest.mark.asyncio
async def test_get_contact_by_phone_uses_cache(repository: ContactRepository) -> None:
    cached = {"id": "123", "phone": "+551199999", "name": "Ana"}
    await repository._cache_contact_data(cached)

    result = await repository.get_contact_by_phone(
        cached["phone"]
    )

    assert result == cached
    # Supabase should not be hit when cache satisfies
    assert repository.supabase.client.table_calls == []


@pytest.mark.asyncio
async def test_get_contact_by_phone_populates_cache(repository: ContactRepository) -> None:
    phone = "+551188888888"
    repo_query = repository.supabase.client.table("contacts")
    repo_query._data = {"id": "456", "phone": phone, "name": "Maria"}

    result = await repository.get_contact_by_phone(phone)

    assert result["id"] == "456"
    cached = await repository.cache.get(f"contact:phone:{phone}")
    assert cached["name"] == "Maria"
