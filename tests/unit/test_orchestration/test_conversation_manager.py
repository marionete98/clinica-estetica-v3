import pytest

from services.orchestration.conversation_manager import ConversationManager


class FakeRedisClient:
    def __init__(self, stored_context=None):
        self.stored_context = stored_context or []
        self.get_calls = []
        self.append_calls = []

    async def get_context(self, conversation_id, max_messages):
        self.get_calls.append((conversation_id, max_messages))
        if isinstance(self.stored_context, Exception):
            raise self.stored_context
        if max_messages is None:
            return list(self.stored_context)
        return list(self.stored_context[-max_messages:])

    async def append_message(self, conversation_id, role, content):
        self.append_calls.append((conversation_id, role, content))
        self.stored_context.append({"role": role, "content": content})
        return True


@pytest.mark.asyncio
async def test_load_context_returns_last_messages():
    redis_client = FakeRedisClient(
        stored_context=[
            {"role": "user", "content": "Oi"},
            {"role": "assistant", "content": "Olá"},
            {"role": "user", "content": "Tudo bem?"},
        ]
    )
    manager = ConversationManager(redis_client)

    result = await manager.load_context("conv-1", max_messages=2)

    assert redis_client.get_calls == [("conv-1", 2)]
    assert result == [
        {"role": "assistant", "content": "Olá"},
        {"role": "user", "content": "Tudo bem?"},
    ]


@pytest.mark.asyncio
async def test_load_context_handles_errors_gracefully():
    redis_client = FakeRedisClient(stored_context=RuntimeError("boom"))
    manager = ConversationManager(redis_client)

    result = await manager.load_context("conv-err", max_messages=5)

    assert result == []


@pytest.mark.asyncio
async def test_append_context_persists_user_and_assistant_messages():
    redis_client = FakeRedisClient()
    manager = ConversationManager(redis_client)

    await manager.append_context("conv-2", "Oi", "Olá, como posso ajudar?")

    assert redis_client.append_calls == [
        ("conv-2", "user", "Oi"),
        ("conv-2", "assistant", "Olá, como posso ajudar?"),
    ]
    assert redis_client.stored_context[-2:] == [
        {"role": "user", "content": "Oi"},
        {"role": "assistant", "content": "Olá, como posso ajudar?"},
    ]
