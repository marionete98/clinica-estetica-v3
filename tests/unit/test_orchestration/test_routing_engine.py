import pytest

from services.orchestration.routing_engine import RouteDecision, RoutingEngine


class StubSupervisor:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def classify_intent(self, *, message, conversation_id, context):
        self.calls.append((message, conversation_id, list(context)))
        return self.response


class StubConversationManager:
    def __init__(self, context):
        self.context = context
        self.calls = []

    async def load_context(self, conversation_id, max_messages):
        self.calls.append((conversation_id, max_messages))
        return list(self.context)


@pytest.mark.asyncio
async def test_determine_route_returns_dataclass_with_expected_values():
    context = [
        {"role": "user", "content": "Oi"},
        {"role": "assistant", "content": "Olá"},
    ]
    supervisor = StubSupervisor(
        response={
            "intent": "faq",
            "agent": "faq",
            "loop_detected": False,
            "confidence": 0.92,
        }
    )
    conversation_manager = StubConversationManager(context)
    engine = RoutingEngine(supervisor, conversation_manager)

    decision = await engine.determine_route(
        conversation_id="conv-123",
        message="Quais são os serviços?",
    )

    assert isinstance(decision, RouteDecision)
    assert decision.intent == "faq"
    assert decision.agent_name == "faq"
    assert decision.loop_detected is False
    assert decision.supervisor_context == context
    assert decision.raw_classification["confidence"] == 0.92
    assert supervisor.calls == [
        ("Quais são os serviços?", "conv-123", context)
    ]
    assert conversation_manager.calls[0][0] == "conv-123"
