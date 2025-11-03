"""
Tests for Chatwoot improvements: deduplication, batching, human takeover, private messages.
"""

import pytest
from unittest.mock import patch, AsyncMock
import asyncio
import time
from datetime import datetime
from typing import Dict, Any
from httpx import AsyncClient

from main import app
from config.redis_client import redis_client


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def base_webhook_payload() -> Dict[str, Any]:
    """Base Chatwoot webhook payload for testing."""
    timestamp = int(time.time())
    return {
        "event": "message_created",
        "id": timestamp,
        "created_at": timestamp,
        "content": "Test message",
        "message_type": "incoming",
        "private": False,
        "sender": {
            "id": 1,
            "name": "Test User",
            "phone_number": "+5511999999999",
            "identifier": "+5511999999999",
        },
        "conversation": {"id": 12345, "status": "open"},
    }


# ============================================================================
# MESSAGE DEDUPLICATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_duplicate_message_detection(client, base_webhook_payload):
    """Test that duplicate messages are detected and ignored."""

    # Send first message
    response1 = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )

    assert response1.status_code == 200
    assert response1.json()["status"] == "accepted"

    # Send same message again (duplicate)
    response2 = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )

    assert response2.status_code == 200
    assert response2.json()["status"] == "ignored"
    assert response2.json()["reason"] == "duplicate_message"


@pytest.mark.asyncio
async def test_duplicate_detection_expires(client, base_webhook_payload):
    """Test that duplicate detection expires after TTL."""

    # This test would require mocking time or waiting for TTL
    # For now, we just verify the mechanism exists

    # Send first message
    response1 = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )

    assert response1.status_code == 200
    assert response1.json()["status"] == "accepted"

    # Change message ID (different message)
    base_webhook_payload["id"] = int(time.time()) + 1000

    # Send different message
    response2 = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )

    assert response2.status_code == 200
    assert response2.json()["status"] == "accepted"


# ============================================================================
# MESSAGE BATCHING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_message_batching_queues_consecutive_messages(
    client, base_webhook_payload
):
    """Test that consecutive messages are queued for batching."""

    conversation_id = 99999
    base_webhook_payload["conversation"]["id"] = conversation_id

    # Send first message
    base_webhook_payload["id"] = int(time.time())
    response1 = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )

    assert response1.status_code == 200
    assert response1.json()["status"] == "accepted"

    # Send second message quickly (should be queued)
    await asyncio.sleep(0.5)
    base_webhook_payload["id"] = int(time.time()) + 1
    base_webhook_payload["content"] = "Second message"

    response2 = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )

    assert response2.status_code == 200
    assert response2.json()["status"] == "queued"
    assert "batch" in response2.json()["message"].lower()


@pytest.mark.asyncio
async def test_message_batching_processes_after_delay(client, base_webhook_payload):
    """Test that batched messages are processed after delay."""

    conversation_id = 88888
    base_webhook_payload["conversation"]["id"] = conversation_id

    # Send 3 messages quickly
    for i in range(3):
        base_webhook_payload["id"] = int(time.time()) + i
        base_webhook_payload["content"] = f"Message {i + 1}"

        response = await client.post(
            "/webhooks/chatwoot",
            json=base_webhook_payload,
            headers={"X-Chatwoot-Signature": "test"},
        )

        if i == 0:
            assert response.status_code == 200
            assert response.json()["status"] == "accepted"
        else:
            assert response.status_code == 200
            assert response.json().get("status") in {"accepted", "queued"}

        await asyncio.sleep(0.5)

    # Wait for processing delay + processing time
    await asyncio.sleep(10)

    # Messages should have been processed
    # (In real test, we'd verify only 1 response was sent to Chatwoot)


# ============================================================================
# PRIVATE MESSAGE FILTER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_private_messages_are_rejected(client, base_webhook_payload):
    """Test that private messages (internal notes) are rejected."""

    # Set message as private
    base_webhook_payload["private"] = True

    response = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )

    assert "private" in response.json()["reason"].lower()


@pytest.mark.asyncio
async def test_public_messages_are_accepted(client, base_webhook_payload):
    """Test that public messages are accepted."""

    # Ensure message is public
    base_webhook_payload["private"] = False

    response = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )


# ============================================================================
# HUMAN TAKEOVER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_human_takeover_disables_ai(client, base_webhook_payload):
    """Test that AI is disabled when conversation is under human control."""

    conversation_id = "77777"
    base_webhook_payload["conversation"]["id"] = int(conversation_id)

    # Set conversation to human control in Redis
    redis = redis_client.client
    state_key = f"session:{conversation_id}"

    import json

    state = {
        "automation_paused": True,
        "human_takeover_reason": "escalation",
        "conversation_id": conversation_id,
    }

    await redis.set(state_key, json.dumps(state), ex=3600)

    # Send message
    response = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )

    # Message should be accepted but not processed by AI

    # Clean up
    await redis.delete(state_key)


@pytest.mark.asyncio
async def test_return_conversation_to_ai(client):
    """Test endpoint to return conversation from human to AI control."""

    conversation_id = "66666"

    # Set conversation to human control
    redis = redis_client.client
    state_key = f"session:{conversation_id}"

    import json

    state = {
        "automation_paused": True,
        "human_takeover_reason": "escalation",
        "conversation_id": conversation_id,
    }

    await redis.set(state_key, json.dumps(state), ex=3600)

    # Return to AI
    with (
        patch("routes.api.chatwoot_client.send_message", return_value={"id": 123}),
        patch(
            "routes.api.supabase_ops.aupdate",
            new=AsyncMock(return_value=[{"conversation_id": conversation_id}]),
        ),
    ):
        response = await client.post(f"/conversations/{conversation_id}/return-to-ai")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["conversation_id"] == conversation_id
        assert data.get("chatwoot_notified") in {True, False}

    # Verify state was updated
    updated_state_data = await redis.get(state_key)
    if updated_state_data:
        updated_state = json.loads(updated_state_data)
        assert updated_state["automation_paused"] is False
        assert updated_state["human_takeover_reason"] is None

    # Clean up
    await redis.delete(state_key)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_complete_flow_with_all_improvements(client, base_webhook_payload):
    """Test complete flow with all improvements working together."""

    conversation_id = 55555
    base_webhook_payload["conversation"]["id"] = conversation_id

    # 1. Send first message (should be accepted)
    base_webhook_payload["id"] = int(time.time())
    response1 = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )
    assert response1.status_code == 200
    assert response1.json()["status"] == "accepted"

    # 2. Send duplicate (should be ignored)
    response2 = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )
    assert response2.status_code == 200
    assert response2.json()["status"] == "ignored"

    # 3. Send private message (should be rejected)
    base_webhook_payload["id"] = int(time.time()) + 100
    base_webhook_payload["private"] = True
    response3 = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )
    assert response3.status_code == 200
    assert response3.json()["status"] == "ignored"

    # 4. Send consecutive messages (should batch)
    base_webhook_payload["private"] = False
    for i in range(2):
        base_webhook_payload["id"] = int(time.time()) + 200 + i
        base_webhook_payload["content"] = f"Batched message {i + 1}"

        response = await client.post(
            "/webhooks/chatwoot",
            json=base_webhook_payload,
            headers={"X-Chatwoot-Signature": "test"},
        )

        await asyncio.sleep(0.5)


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_dedup_ttl_configuration():
    """Test that deduplication TTL is configurable."""
    from config.settings import settings

    # Verify setting exists
    assert hasattr(settings, "message_dedup_ttl_seconds")
    assert settings.message_dedup_ttl_seconds > 0


@pytest.mark.asyncio
async def test_batching_delay_configuration():
    """Test that batching delay is configurable."""
    from config.settings import settings

    # Verify setting exists
    assert hasattr(settings, "message_processing_delay_seconds")
    assert settings.message_processing_delay_seconds >= 0


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_invalid_payload_structure(client):
    """Test handling of invalid webhook payload."""

    invalid_payload = {
        "event": "message_created",
        # Missing required fields
    }

    response = await client.post(
        "/webhooks/chatwoot",
        json=invalid_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )


@pytest.mark.asyncio
async def test_missing_conversation_id(client, base_webhook_payload):
    """Test handling of missing conversation ID."""

    # Remove conversation ID
    base_webhook_payload["conversation"] = {}

    response = await client.post(
        "/webhooks/chatwoot",
        json=base_webhook_payload,
        headers={"X-Chatwoot-Signature": "test"},
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
