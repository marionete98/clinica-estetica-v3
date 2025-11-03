"""Pytest fixtures shared across repository unit tests."""

from __future__ import annotations

import asyncio
from typing import Iterator

import pytest

from ._helpers import FakeSupabase


@pytest.fixture(autouse=True)
def _sync_asyncio_to_thread(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Make ``asyncio.to_thread`` synchronous for deterministic tests."""

    monkeypatch.setattr(asyncio, "to_thread", lambda func, *a, **kw: func(*a, **kw))
    yield


@pytest.fixture
def fake_supabase() -> FakeSupabase:
    """Return a new fake supabase client wrapper."""

    return FakeSupabase()
