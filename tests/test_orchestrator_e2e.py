"""Integration-style tests for the refactored agent orchestrator."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from services.orchestration.orchestrator import AgentOrchestrator


class FakeRedisClient:
    def __init__(self) -> None:
        self.context: Dict[str, List[Dict[str, str]]] = {}
        self.appended: List[tuple[str, str, str]] = []

    async def get_context(self, conversation_id: str, max_messages: int) -> List[Dict[str, str]]:
        return self.context.get(conversation_id, [])[-max_messages:]

    async def append_message(self, conversation_id: str, role: str, content: str) -> bool:
        self.appended.append((conversation_id, role, content))
        self.context.setdefault(conversation_id, []).append({"role": role, "content": content})
        return True

    async def get_value(self, key: str, deserialize: bool = True) -> Any:  # noqa: ARG002
        return None

    async def set_value(self, key: str, value: Any, ttl: int | None = None) -> None:  # noqa: ARG002
        return None


class FakeSupabaseOps:
    async def aselect(self, **kwargs: Any) -> List[Dict[str, Any]]:  # noqa: ARG002
        return []


class StubSupervisor:
    async def classify_intent(self, *, message: str, conversation_id: str, context: List[Dict[str, str]]) -> Dict[str, Any]:  # noqa: D401, D403
        return {
            "intent": "greeting",
            "agent": "intake",
            "loop_detected": False,
            "confidence": 0.95,
        }


class StubIntakeAgent:
    async def process_message(self, *, message: str, phone: str, context: List[Dict[str, str]]) -> Dict[str, Any]:  # noqa: D401, D403
        return {
            "response": f"Olá, {phone}! Você disse: {message}",
            "metadata": {"handled_by": "intake"},
            "should_escalate": False,
        }


class StubFAQAgent:
    async def answer_question(self, *, question: str, contact_name: str | None, context: List[Dict[str, str]]) -> Dict[str, Any]:  # noqa: D401, D403
        return {
            "response": "Resposta FAQ",
            "metadata": {},
            "should_escalate": False,
        }


class StubSchedulerAgent:
    async def process_request(self, **kwargs: Any) -> Dict[str, Any]:  # noqa: D401, D403
        return {
            "response": "[ACTION:BOOK][BOOKING_ID:abc123] Horário reservado",
            "metadata": {},
            "should_escalate": False,
        }


class StubEscalationAgent:
    async def prepare_escalation(self, **kwargs: Any) -> Dict[str, Any]:  # noqa: D401, D403
        return {
            "response": "Encaminhando para humano",
            "metadata": {},
            "should_escalate": True,
        }


class StubAgentFactory:
    def __init__(self) -> None:
        self.default_llm_config: Dict[str, Any] = {
            "provider": "test",
        }

    def create_supervisor(self) -> StubSupervisor:
        return StubSupervisor()

    def create_intake(self) -> StubIntakeAgent:
        return StubIntakeAgent()

    def create_faq(self) -> StubFAQAgent:
        return StubFAQAgent()

    def create_scheduler(self) -> StubSchedulerAgent:
        return StubSchedulerAgent()

    def create_escalation(self) -> StubEscalationAgent:
        return StubEscalationAgent()

    def create_followup(self):  # pragma: no cover - not used in test
        return SimpleNamespace(cleanup=lambda: None)


@pytest.mark.asyncio
async def test_orchestrator_routes_message_and_persists_context() -> None:
    redis = FakeRedisClient()
    supabase = FakeSupabaseOps()
    factory = StubAgentFactory()

    orchestrator = AgentOrchestrator(
        agent_factory=factory,
        redis_client=redis,
        supabase_ops=supabase,
    )

    payload = await orchestrator.orchestrate(
        conversation_id="conv-1",
        phone="+5511999999999",
        message="Oi, tudo bem?",
    )

    assert payload["agent"] == "intake"
    assert payload["response"].startswith("Olá, +5511999999999!")
    assert redis.appended[-1] == (
        "conv-1",
        "assistant",
        payload["response"],
    )
