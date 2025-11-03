"""Shared helpers for repository unit tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, Optional


class FakeQuery:
    """Very small supabase query stub used in repository tests."""

    def __init__(self, data: Optional[Dict[str, Any]] = None) -> None:
        self._data = data or {}
        self.history: list[tuple[str, Dict[str, Any]]] = []

    def select(self, *_args: Any, **_kwargs: Any) -> "FakeQuery":
        return self

    def update(self, payload: Dict[str, Any]) -> "FakeQuery":
        self.history.append(("update", payload))
        self._data.update(payload)
        return self

    def insert(self, payload: Dict[str, Any]) -> "FakeQuery":
        self.history.append(("insert", payload))
        self._data = {**payload}
        self._data.setdefault("id", "generated-id")
        return self

    def eq(self, *_args: Any, **_kwargs: Any) -> "FakeQuery":
        return self

    def order(self, *_args: Any, **_kwargs: Any) -> "FakeQuery":
        return self

    def gte(self, *_args: Any, **_kwargs: Any) -> "FakeQuery":
        return self

    def lte(self, *_args: Any, **_kwargs: Any) -> "FakeQuery":
        return self

    def execute(self) -> SimpleNamespace:
        data = []
        if isinstance(self._data, list):
            data = self._data
        elif self._data:
            data = [self._data]
        return SimpleNamespace(data=data)


class FakeSupabaseClient:
    """Minimal supabase client stub returning :class:`FakeQuery` objects."""

    def __init__(self) -> None:
        self.table_calls: list[str] = []
        self._tables: Dict[str, FakeQuery] = {}

    def table(self, name: str) -> FakeQuery:
        self.table_calls.append(name)
        return self._tables.setdefault(name, FakeQuery())


class FakeSupabase:
    """Container matching the real supabase client attribute used in repos."""

    def __init__(self) -> None:
        self.client = FakeSupabaseClient()
