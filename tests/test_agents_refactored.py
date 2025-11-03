"""High-level tests covering refactored FAQ agent orchestration."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from agents.faq.faq_agent import FAQAgent
from config.llm_config import create_llm_config


class DummyAssistant:
    """Minimal assistant stub that returns deterministic responses."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401, D403
        self.calls: List[str] = []

    async def run(self, task: str, cancellation_token: Any) -> SimpleNamespace:  # type: ignore[override]
        self.calls.append(task)
        return SimpleNamespace(messages=[SimpleNamespace(content="Resposta definitiva")])


class DummyCache:
    def __init__(self, initial: Dict[str, Dict[str, Any]] | None = None) -> None:
        self.storage = initial or {}

    async def get(self, key: str) -> Dict[str, Any] | None:
        return self.storage.get(key)

    async def set(self, key: str, value: Dict[str, Any], ttl: int | None = None) -> None:  # noqa: ARG002
        self.storage[key] = value


class StubKnowledgeRepository:
    async def search(self, keywords: List[str]) -> List[SimpleNamespace]:
        return [
            SimpleNamespace(
                title="Depilação a Laser",
                content="Tratamento com resultados rápidos",
                category="tratamentos",
            )
        ]


class StubTemplateRepository:
    async def get(self, name: str) -> SimpleNamespace | None:
        return SimpleNamespace(name=name, content="Template padrão")


@pytest.fixture(autouse=True)
def _patch_assistant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agents.faq.faq_agent.AssistantAgent", DummyAssistant)
    monkeypatch.setattr("agents.faq.faq_agent.create_model_client", lambda config: object())


@pytest.mark.asyncio
async def test_answer_question_returns_cached_response() -> None:
    cache = DummyCache({"Quanto custa?": {"answer": "R$ 100", "metadata": {}}})

    agent = FAQAgent(
        llm_config=create_llm_config(provider="xai", api_key="key", model="grok"),
        knowledge_repository=StubKnowledgeRepository(),
        template_repository=StubTemplateRepository(),
        cache=cache,
        knowledge_memory=None,
    )

    result = await agent.answer_question("Quanto custa?", contact_name="Ana")

    assert result["answer"] == "R$ 100"
    assert result["cached"] is True
    assert agent.agent.calls == []


@pytest.mark.asyncio
async def test_answer_question_generates_and_caches_response() -> None:
    cache = DummyCache()

    agent = FAQAgent(
        llm_config=create_llm_config(provider="xai", api_key="key", model="grok"),
        knowledge_repository=StubKnowledgeRepository(),
        template_repository=StubTemplateRepository(),
        cache=cache,
        knowledge_memory=None,
    )

    result = await agent.answer_question("Qual é o preço da depilação?")

    assert result["confidence"] == "high"
    assert cache.storage  # Cache should be populated after successful answer
    stored_answer = next(iter(cache.storage.values()))
    assert stored_answer["answer"].startswith("Resposta definitiva")
