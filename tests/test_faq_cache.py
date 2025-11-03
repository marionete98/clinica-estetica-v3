"""
Async tests for FAQ Agent cache functionality with Redis (mocked).
Covers: hit/miss, expiration, clear_cache, get_cache_stats, warm_cache, and concurrency.
Also verifies agent-level caching behavior for high vs low confidence.
"""

import asyncio
import json
import time
from typing import Any, Optional, Dict, Tuple, List

import pytest

# Import after pytest to allow monkeypatching of module-level singletons
from agents import faq as faq_mod
from agents.faq import FAQAgent, RedisFAQCache
from tools import kb_tools_cached as kb_mod


class FakeRedisClient:
    """In-memory async Redis stub with TTL support and minimal API surface."""

    def __init__(self):
        # key -> (value_str, expire_ts or None)
        self._store: Dict[str, Tuple[str, Optional[float]]] = {}
        # Expose a simple client API used by RedisFAQCache: keys(), delete()
        self.client = self

    # ----- Helpers -----
    def _now(self) -> float:
        return time.time()

    def _expired(self, key: str) -> bool:
        if key not in self._store:
            return False
        _, exp = self._store[key]
        return exp is not None and self._now() >= exp

    def _gc_if_expired(self, key: str) -> None:
        if self._expired(key):
            self._store.pop(key, None)

    # ----- High-level API used by RedisFAQCache -----
    async def set_value(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not isinstance(value, str):
            value = json.dumps(value)
        expire_ts = self._now() + ttl if ttl else None
        self._store[key] = (value, expire_ts)
        return True

    async def get_value(self, key: str, deserialize: bool = True) -> Optional[Any]:
        self._gc_if_expired(key)
        if key not in self._store:
            return None
        value_str, _ = self._store[key]
        if deserialize:
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                return value_str
        return value_str

    # ----- Raw client methods used by RedisFAQCache -----
    async def keys(self, pattern: str) -> List[str]:
        # Only pattern used is f"{prefix}*"; implement startswith matching
        prefix = pattern[:-1] if pattern.endswith("*") else pattern
        # GC expired first
        for k in list(self._store.keys()):
            self._gc_if_expired(k)
        return [k for k in self._store.keys() if k.startswith(prefix)]

    async def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                count += 1
        return count


@pytest.fixture()
def fake_redis(monkeypatch):
    """Monkeypatch agents.faq.redis_client with our in-memory fake before each test."""
    fake = FakeRedisClient()
    monkeypatch.setattr(faq_mod, "redis_client", fake, raising=True)
    return fake


@pytest.mark.asyncio
async def test_cache_set_and_get(fake_redis):
    cache = RedisFAQCache(ttl_seconds=3600, max_size=100)

    q = "Quanto custa a depilação a laser?"
    resp = {"answer": "Valores...", "confidence": "high", "cached": False}

    await cache.set(q, resp)
    cached = await cache.get(q)

    assert cached is not None
    assert cached["answer"] == resp["answer"]
    assert cached["confidence"] == resp["confidence"]


@pytest.mark.asyncio
async def test_cache_miss(fake_redis):
    cache = RedisFAQCache()
    result = await cache.get("Pergunta inexistente")
    assert result is None


@pytest.mark.asyncio
async def test_cache_only_high_confidence(fake_redis):
    cache = RedisFAQCache()

    q = "Alguma pergunta"
    low = {"answer": "Não tenho certeza", "confidence": "low"}
    await cache.set(q, low)

    stats = await cache.get_stats()
    assert stats["current_size"] == 0

    high = {"answer": "Resposta", "confidence": "high"}
    await cache.set(q, high)

    stats = await cache.get_stats()
    assert stats["current_size"] == 1


@pytest.mark.asyncio
async def test_cache_ttl_expiration(fake_redis):
    cache = RedisFAQCache(ttl_seconds=1)
    q = "Pergunta TTL"
    v = {"answer": "A", "confidence": "high"}

    await cache.set(q, v)
    assert await cache.get(q) is not None

    await asyncio.sleep(1.5)
    assert await cache.get(q) is None


@pytest.mark.asyncio
async def test_cache_stats_and_clear(fake_redis):
    cache = RedisFAQCache(ttl_seconds=3600, max_size=100)

    # Add some entries
    for i in range(5):
        await cache.set(f"Q{i}", {"answer": f"A{i}", "confidence": "high"})

    # Hits and misses
    assert await cache.get("Q0") is not None
    assert await cache.get("Q1") is not None
    assert await cache.get("NonExistent") is None

    stats = await cache.get_stats()
    assert stats["current_size"] == 5
    assert stats["max_size"] == 100
    assert stats["hits"] == 2
    assert stats["misses"] == 1
    assert stats["ttl_seconds"] == 3600
    assert 0 <= stats["hit_rate"] <= 1

    # Clear
    await cache.clear()
    stats = await cache.get_stats()
    assert stats["current_size"] == 0
    assert stats["hits"] == 0
    assert stats["misses"] == 0


@pytest.mark.asyncio
async def test_warm_cache_with_common_questions(monkeypatch, fake_redis):
    # Patch underlying LLM call to produce high-confidence responses and avoid real KB access
    class DummyRunResult:
        def __init__(self, text: str):
            self.messages = [type("M", (), {"content": text})()]

    async def fake_run_high(task: str):
        return DummyRunResult("Resposta confiável")

    async def fake_kb_search(query: str, top_k: int = 3, category: Optional[str] = None):
        return [], []

    agent = FAQAgent({"provider": "xai", "api_key": "test", "model": "grok-4-reasoning"}, enable_cache=True)

    monkeypatch.setattr(agent.agent, "run", fake_run_high, raising=True)
    # Patch function imported directly in agents.faq
    monkeypatch.setattr(faq_mod, "search_knowledge_base", fake_kb_search, raising=True)

    qs = [
        "Quanto custa a depilação a laser?",
        "Qual o horário de funcionamento?",
        "Vocês fazem botox?",
    ]
    await agent.warm_cache(qs)

    stats = await agent.get_cache_stats()
    assert stats is not None
    assert stats["current_size"] >= 3


@pytest.mark.asyncio
async def test_concurrent_cache_access(fake_redis):
    cache = RedisFAQCache()

    async def writer(i: int):
        await cache.set(f"Q{i}", {"answer": f"A{i}", "confidence": "high"})

    async def reader(i: int):
        await cache.get(f"Q{i}")

    tasks = []
    for i in range(20):
        tasks.append(writer(i))
        tasks.append(reader(i))
    await asyncio.gather(*tasks)

    stats = await cache.get_stats()
    assert stats["current_size"] == 20


@pytest.mark.asyncio
async def test_agent_caches_high_confidence_and_skips_low(monkeypatch, fake_redis):
    # Prepare agent
    agent = FAQAgent({"provider": "xai", "api_key": "test", "model": "grok-4-reasoning"}, enable_cache=True)

    class DummyRunResult:
        def __init__(self, text: str):
            self.messages = [type("M", (), {"content": text})()]

    # Patch agent.run to simulate LLM responses and KB search to avoid Redis
    async def fake_run_high(task: str):
        return DummyRunResult("Resposta confiável")

    async def fake_run_low(task: str):
        return DummyRunResult("Resposta incerta ESCALATE_LOW_CONFIDENCE")

    async def fake_kb_search(query: str, top_k: int = 3, category: Optional[str] = None):
        return [], []

    # Monkeypatch the agent's underlying AssistantAgent.run and KB search
    monkeypatch.setattr(agent.agent, "run", fake_run_high, raising=True)
    monkeypatch.setattr(faq_mod, "search_knowledge_base", fake_kb_search, raising=True)

    q = "Pergunta de preço"
    result1 = await agent.answer_question(q)
    assert result1["confidence"] == "high"

    # Second call should hit cache and include cached=True
    result2 = await agent.answer_question(q)
    assert result2.get("cached") is True

    # Now switch to low confidence and ensure it is not cached under a new question
    monkeypatch.setattr(agent.agent, "run", fake_run_low, raising=True)
    q2 = "Outra pergunta"
    result3 = await agent.answer_question(q2)
    assert result3["confidence"] == "low"

    # Ensure low confidence did not cache
    cached_low = await agent._cache.get(q2)
    assert cached_low is None

