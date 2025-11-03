"""Unit tests for the in-memory MemoryStore implementation."""

from __future__ import annotations

import asyncio

import pytest

from services.memory.in_memory_store import InMemoryStore


@pytest.fixture
async def memory() -> InMemoryStore:
    store = InMemoryStore()
    yield store
    await store.close()


@pytest.mark.asyncio
async def test_set_and_get_round_trip(memory: InMemoryStore) -> None:
    await memory.set("key", {"value": 1})
    result = await memory.get("key")
    assert result == {"value": 1}


@pytest.mark.asyncio
async def test_ttl_expiration(memory: InMemoryStore) -> None:
    await memory.set("ephemeral", "value", ttl=1)
    await asyncio.sleep(1.1)
    assert await memory.get("ephemeral") is None


@pytest.mark.asyncio
async def test_invalidate_pattern(memory: InMemoryStore) -> None:
    await memory.set("cache:1", 1)
    await memory.set("cache:2", 2)
    removed = await memory.invalidate_pattern("cache:*")
    assert removed == 2


@pytest.mark.asyncio
async def test_increment_initializes_value(memory: InMemoryStore) -> None:
    new_value = await memory.increment("counter")
    assert new_value == 1
    new_value = await memory.increment("counter", amount=2)
    assert new_value == 3
