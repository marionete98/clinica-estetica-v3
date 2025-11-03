from types import SimpleNamespace

import pytest

from services.orchestration.agent_coordinator import (
    AgentCallResult,
    AgentCoordinator,
)
from services.orchestration.routing_engine import RouteDecision


class DummyRedis:
    def __init__(self):
        self.storage = {}

    async def get_value(self, key, deserialize=True):
        return self.storage.get(key)

    async def set_value(self, key, value, ttl=None):
        self.storage[key] = value


class DummySupabase:
    async def aselect(self, **kwargs):
        return []


@pytest.mark.asyncio
async def test_execute_returns_normalized_result(monkeypatch):
    coordinator = AgentCoordinator(
        agent_pool=SimpleNamespace(),
        redis_client=DummyRedis(),
        supabase_ops=DummySupabase(),
    )
    decision = RouteDecision(
        intent="faq",
        agent_name="faq",
        loop_detected=False,
        supervisor_context=[],
        raw_classification={"agent": "faq"},
    )

    async def fake_call(agent_name, call):
        assert agent_name == "faq"
        return AgentCallResult(
            payload={
                "response": "Olá!",
                "metadata": {"source": "kb"},
                "should_escalate": False,
            },
            context_key="faq",
            context_size=3,
        )

    monkeypatch.setattr(coordinator, "_call_with_retry", fake_call)

    result = await coordinator.execute(
        decision=decision,
        conversation_id="conv-55",
        phone="+5511999999999",
        message="Oi",
        conversation_manager=SimpleNamespace(),
        default_confidence="medium",
    )

    assert result.response_text == "Olá!"
    assert result.should_escalate is False
    assert result.metadata["source"] == "kb"
    assert result.context_usage == {"faq": 3}


@pytest.mark.asyncio
async def test_execute_scheduler_populates_booking_metadata(monkeypatch):
    coordinator = AgentCoordinator(
        agent_pool=SimpleNamespace(),
        redis_client=DummyRedis(),
        supabase_ops=DummySupabase(),
    )
    decision = RouteDecision(
        intent="schedule",
        agent_name="scheduler",
        loop_detected=False,
        supervisor_context=[],
        raw_classification={"agent": "scheduler"},
    )

    async def fake_call(agent_name, call):
        assert agent_name == "scheduler"
        return await call()

    async def fake_invoke(**kwargs):
        return AgentCallResult(
            payload={
                "response": "Horário confirmado.",
                "metadata": {},
                "action": "book",
                "requires_confirmation": True,
            },
            context_key="scheduler",
            context_size=2,
            booking_id="abc123",
        )

    monkeypatch.setattr(coordinator, "_call_with_retry", fake_call)
    monkeypatch.setattr(coordinator, "_invoke_agent", fake_invoke)

    result = await coordinator.execute(
        decision=decision,
        conversation_id="conv-22",
        phone="+5511888888888",
        message="Quero agendar",
        conversation_manager=SimpleNamespace(),
        default_confidence="high",
    )

    assert result.metadata["action"] == "book"
    assert result.booking_id == "abc123"
    assert result.raw_response["booking_id"] == "abc123"
    assert result.raw_response["metadata"]["requires_confirmation"] is True


def test_parse_scheduler_response_extracts_tokens():
    text = "[ACTION:CANCEL][BOOKING_ID:xyz789] Mensagem"
    parsed = AgentCoordinator._parse_scheduler_response(text)

    assert parsed == {
        "response_text": "Mensagem",
        "action": "cancel",
        "booking_id": "xyz789",
    }
