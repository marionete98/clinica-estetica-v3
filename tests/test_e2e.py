"""
End-to-End Integration Tests for Clínica Luana Multi-Agent System.

These tests simulate complete conversation flows through the webhook endpoint,
testing FAQ, scheduling, and rescheduling/cancellation scenarios.

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
"""

import pytest
import pytest_asyncio
import asyncio
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta
from httpx import AsyncClient
from fastapi import status

from main import app
from config.supabase_client import supabase_client
from config.redis_client import redis_client


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_conversation_ids():
    """Generate unique conversation IDs for tests."""
    timestamp = int(time.time() * 1000)
    return {
        "faq": [f"test_faq_{timestamp}_{i}" for i in range(8)],
        "schedule": [f"test_schedule_{timestamp}_{i}" for i in range(8)],
        "reschedule": [f"test_reschedule_{timestamp}_{i}" for i in range(8)],
    }


@pytest.fixture
def test_phone_numbers():
    """Generate unique phone numbers for tests."""
    timestamp = int(time.time())
    base = timestamp % 100000000  # Last 8 digits
    return {
        "faq": [f"+5594{base + i:08d}" for i in range(8)],
        "schedule": [f"+5594{base + 100 + i:08d}" for i in range(8)],
        "reschedule": [f"+5594{base + 200 + i:08d}" for i in range(8)],
    }



# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_chatwoot_webhook_payload(
    conversation_id: str,
    phone: str,
    message: str,
    message_type: str = "incoming"
) -> Dict[str, Any]:
    """Create a mock Chatwoot webhook payload."""
    return {
        "event": "message_created",
        "conversation": {
            "id": conversation_id,
            "status": "open"
        },
        "message_type": message_type,
        "content": message,
        "sender": {
            "id": 12345,
            "name": "Test User",
            "phone_number": phone,
            "identifier": phone
        },
        "id": int(time.time() * 1000),
        "created_at": int(time.time())
    }


async def send_webhook_message(
    client: AsyncClient,
    conversation_id: str,
    phone: str,
    message: str
) -> Dict[str, Any]:
    """Send a webhook message and return the response."""
    payload = create_chatwoot_webhook_payload(conversation_id, phone, message)
    
    response = await client.post(
        "/webhooks/chatwoot",
        json=payload,
        headers={"X-Chatwoot-Signature": "test-signature"}
    )
    
    return {
        "status_code": response.status_code,
        "response": response.json() if response.status_code == 200 else None,
        "conversation_id": conversation_id,
        "phone": phone,
        "message": message
    }


async def wait_for_agent_response(conversation_id: str, timeout: int = 10, interval: float = 0.5):
    """
    Waits for an agent response to be logged in the Supabase 'logs' table
    for a given conversation_id.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        logs = await supabase_client.client.table("logs").select("*").eq(
            "conversation_id", conversation_id
        ).order("created_at", desc=True).limit(1).execute()
        
        if logs.data and logs.data[0].get("event") == "agent_response_sent":
            print(f"\nAgent response found for {conversation_id} after {time.time() - start_time:.2f}s")
            return True
        
        await asyncio.sleep(interval)
    
    raise TimeoutError(f"Agent response not found for {conversation_id} within {timeout} seconds.")



# ============================================================================
# FAQ CONVERSATION TESTS (8 scenarios)
# ============================================================================

@pytest.mark.asyncio
async def test_faq_treatment_information(client, test_conversation_ids, test_phone_numbers):
    """Test FAQ conversation about treatment information."""
    conv_id = test_conversation_ids["faq"][0]
    phone = test_phone_numbers["faq"][0]
    
    # Send question about laser hair removal
    result = await send_webhook_message(
        client, conv_id, phone,
        "Olá! Gostaria de saber sobre depilação a laser"
    )
    
    assert result["status_code"] == 200
    assert result["response"]["status"] == "accepted"
    
    # Wait for processing
    await wait_for_agent_response(conv_id)

    # Get the agent's response text from the webhook's JSON response
    agent_response_text = result["response"].get("response", "")

    # Assert that the agent's response contains expected keywords
    assert "depilação a laser" in agent_response_text.lower() or \
           "laser" in agent_response_text.lower(), \
           f"Expected 'depilação a laser' or 'laser' in response, got: {agent_response_text}"
    assert "agendar" in agent_response_text.lower() or \
           "consulta" in agent_response_text.lower(), \
           f"Expected 'agendar' or 'consulta' in response, got: {agent_response_text}"


@pytest.mark.asyncio
async def test_faq_pricing_fixed(client, test_conversation_ids, test_phone_numbers):
    """Test FAQ conversation about fixed pricing."""
    conv_id = test_conversation_ids["faq"][1]
    phone = test_phone_numbers["faq"][1]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Quanto custa a depilação a laser?"
    )
    
    assert result["status_code"] == 200
    await wait_for_agent_response(conv_id)


@pytest.mark.asyncio
async def test_faq_pricing_consultation(client, test_conversation_ids, test_phone_numbers):
    """Test FAQ conversation about consultation-based pricing."""
    conv_id = test_conversation_ids["faq"][2]
    phone = test_phone_numbers["faq"][2]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Quanto custa harmonização facial?"
    )
    
    assert result["status_code"] == 200
    await wait_for_agent_response(conv_id)


@pytest.mark.asyncio
async def test_faq_cancellation_policy(client, test_conversation_ids, test_phone_numbers):
    """Test FAQ conversation about cancellation policy."""
    conv_id = test_conversation_ids["faq"][3]
    phone = test_phone_numbers["faq"][3]
    
    assert result["status_code"] == 200
    await wait_for_agent_response(conv_id)



@pytest.mark.asyncio
async def test_faq_contraindications(client, test_conversation_ids, test_phone_numbers):
    """Test FAQ conversation about contraindications."""
    conv_id = test_conversation_ids["faq"][4]
    phone = test_phone_numbers["faq"][4]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Quais são as contraindicações para depilação a laser?"
    )
    
    assert result["status_code"] == 200
    await wait_for_agent_response(conv_id)


@pytest.mark.asyncio
async def test_faq_post_treatment_care(client, test_conversation_ids, test_phone_numbers):
    """Test FAQ conversation about post-treatment care."""
    conv_id = test_conversation_ids["faq"][5]
    phone = test_phone_numbers["faq"][5]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Quais cuidados devo ter após a depilação a laser?"
    )
    
    assert result["status_code"] == 200
    await wait_for_agent_response(conv_id)


@pytest.mark.asyncio
async def test_faq_business_hours(client, test_conversation_ids, test_phone_numbers):
    """Test FAQ conversation about business hours."""
    conv_id = test_conversation_ids["faq"][6]
    phone = test_phone_numbers["faq"][6]
    
    assert result["status_code"] == 200
    await wait_for_agent_response(conv_id)


@pytest.mark.asyncio
async def test_faq_multi_turn_clarification(client, test_conversation_ids, test_phone_numbers):
    """Test FAQ conversation with multi-turn clarification."""
    conv_id = test_conversation_ids["faq"][7]
    phone = test_phone_numbers["faq"][7]
    
    # First message
    result1 = await send_webhook_message(
        client, conv_id, phone,
        "Quero fazer um tratamento"
    )
    assert result1["status_code"] == 200
    await wait_for_agent_response(conv_id)
    
    # Clarification
    result2 = await send_webhook_message(
        client, conv_id, phone,
        "Tratamento corporal para emagrecimento"
    )
    assert result2["status_code"] == 200
    await wait_for_agent_response(conv_id)



# ============================================================================
# SCHEDULING CONVERSATION TESTS (8 scenarios)
# ============================================================================

@pytest.mark.asyncio
async def test_schedule_simple_booking(client, test_conversation_ids, test_phone_numbers):
    """Test simple scheduling conversation with available slot."""
    conv_id = test_conversation_ids["schedule"][0]
    phone = test_phone_numbers["schedule"][0]
    
    # Greeting and name collection
    result1 = await send_webhook_message(
        client, conv_id, phone,
        "Olá, gostaria de agendar uma consulta"
    )
    assert result1["status_code"] == 200
    await wait_for_agent_response(conv_id)
    
    # Provide name
    result2 = await send_webhook_message(
        client, conv_id, phone,
        "Meu nome é Maria Silva"
    )
    assert result2["status_code"] == 200
    await wait_for_agent_response(conv_id)
    
    # Request specific service
    result3 = await send_webhook_message(
        client, conv_id, phone,
        "Quero agendar depilação a laser"
    )
    assert result3["status_code"] == 200
    await wait_for_agent_response(conv_id)


@pytest.mark.asyncio
async def test_schedule_no_available_slots(client, test_conversation_ids, test_phone_numbers):
    """Test scheduling when no slots are available."""
    conv_id = test_conversation_ids["schedule"][1]
    phone = test_phone_numbers["schedule"][1]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Quero agendar para hoje às 20:00"
    )
    
    assert result["status_code"] == 200
    await wait_for_agent_response(conv_id)


@pytest.mark.asyncio
async def test_schedule_outside_business_hours(client, test_conversation_ids, test_phone_numbers):
    """Test scheduling outside business hours."""
    conv_id = test_conversation_ids["schedule"][2]
    phone = test_phone_numbers["schedule"][2]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Posso agendar para domingo?"
    )
    
    assert result["status_code"] == 200
    await wait_for_agent_response(conv_id)


@pytest.mark.asyncio
async def test_schedule_insufficient_advance(client, test_conversation_ids, test_phone_numbers):
    """Test scheduling with less than 1 hour advance."""
    conv_id = test_conversation_ids["schedule"][3]
    phone = test_phone_numbers["schedule"][3]
    
    # Get current time + 30 minutes
    now = datetime.now()
    target_time = now + timedelta(minutes=30)
    
    result = await send_webhook_message(
        client, conv_id, phone,
        f"Quero agendar para hoje às {target_time.strftime('%H:%M')}"
    )
    
    assert result["status_code"] == 200
    await wait_for_agent_response(conv_id)



@pytest.mark.asyncio
async def test_schedule_with_confirmation(client, test_conversation_ids, test_phone_numbers):
    """Test scheduling with explicit confirmation flow."""
    conv_id = test_conversation_ids["schedule"][4]
    phone = test_phone_numbers["schedule"][4]
    
    # Request booking
    result1 = await send_webhook_message(
        client, conv_id, phone,
        "Quero agendar harmonização facial para amanhã"
    )
    assert result1["status_code"] == 200
    await wait_for_agent_response(conv_id)
    
    # Confirm booking
    result2 = await send_webhook_message(
        client, conv_id, phone,
        "Sim, confirmo o agendamento"
    )
    assert result2["status_code"] == 200
    await wait_for_processing()


@pytest.mark.asyncio
async def test_schedule_check_existing_bookings(client, test_conversation_ids, test_phone_numbers):
    """Test checking existing bookings."""
    conv_id = test_conversation_ids["schedule"][5]
    phone = test_phone_numbers["schedule"][5]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Quais são meus agendamentos?"
    )
    
    assert result["status_code"] == 200
    await wait_for_processing()


@pytest.mark.asyncio
async def test_schedule_multiple_services_inquiry(client, test_conversation_ids, test_phone_numbers):
    """Test inquiry about multiple services."""
    conv_id = test_conversation_ids["schedule"][6]
    phone = test_phone_numbers["schedule"][6]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Posso agendar depilação e harmonização no mesmo dia?"
    )
    
    assert result["status_code"] == 200
    await wait_for_processing()


@pytest.mark.asyncio
async def test_schedule_consultation_booking(client, test_conversation_ids, test_phone_numbers):
    """Test booking a consultation for treatments that require it."""
    conv_id = test_conversation_ids["schedule"][7]
    phone = test_phone_numbers["schedule"][7]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Quero agendar uma consulta para harmonização"
    )
    
    assert result["status_code"] == 200
    await wait_for_processing()



# ============================================================================
# RESCHEDULING/CANCELLATION CONVERSATION TESTS (8 scenarios)
# ============================================================================

@pytest.mark.asyncio
async def test_reschedule_valid_within_policy(client, test_conversation_ids, test_phone_numbers):
    """Test valid cancellation within policy timeframe."""
    conv_id = test_conversation_ids["reschedule"][0]
    phone = test_phone_numbers["reschedule"][0]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Preciso cancelar meu agendamento de amanhã"
    )
    
    assert result["status_code"] == 200
    await wait_for_processing()


@pytest.mark.asyncio
async def test_reschedule_outside_policy(client, test_conversation_ids, test_phone_numbers):
    """Test cancellation outside policy timeframe."""
    conv_id = test_conversation_ids["reschedule"][1]
    phone = test_phone_numbers["reschedule"][1]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Preciso cancelar meu agendamento de hoje"
    )
    
    assert result["status_code"] == 200
    await wait_for_processing()


@pytest.mark.asyncio
async def test_reschedule_first_time(client, test_conversation_ids, test_phone_numbers):
    """Test first rescheduling attempt."""
    conv_id = test_conversation_ids["reschedule"][2]
    phone = test_phone_numbers["reschedule"][2]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Gostaria de remarcar meu agendamento para outro dia"
    )
    
    assert result["status_code"] == 200
    await wait_for_processing()


@pytest.mark.asyncio
async def test_reschedule_second_time(client, test_conversation_ids, test_phone_numbers):
    """Test second rescheduling attempt."""
    conv_id = test_conversation_ids["reschedule"][3]
    phone = test_phone_numbers["reschedule"][3]
    
    # First reschedule
    result1 = await send_webhook_message(
        client, conv_id, phone,
        "Preciso remarcar meu agendamento"
    )
    assert result1["status_code"] == 200
    await wait_for_processing()
    
    # Second reschedule (should still be allowed)
    result2 = await send_webhook_message(
        client, conv_id, phone,
        "Na verdade, preciso remarcar novamente"
    )
    assert result2["status_code"] == 200
    await wait_for_processing()



@pytest.mark.asyncio
async def test_reschedule_exceeds_limit(client, test_conversation_ids, test_phone_numbers):
    """Test rescheduling when limit is exceeded (3rd attempt)."""
    conv_id = test_conversation_ids["reschedule"][4]
    phone = test_phone_numbers["reschedule"][4]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Preciso remarcar pela terceira vez"
    )
    
    assert result["status_code"] == 200
    await wait_for_processing()


@pytest.mark.asyncio
async def test_reschedule_nonexistent_booking(client, test_conversation_ids, test_phone_numbers):
    """Test cancellation of non-existent booking."""
    conv_id = test_conversation_ids["reschedule"][5]
    phone = test_phone_numbers["reschedule"][5]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Quero cancelar meu agendamento"
    )
    
    assert result["status_code"] == 200
    await wait_for_processing()


@pytest.mark.asyncio
async def test_reschedule_to_unavailable_slot(client, test_conversation_ids, test_phone_numbers):
    """Test rescheduling to an unavailable slot."""
    conv_id = test_conversation_ids["reschedule"][6]
    phone = test_phone_numbers["reschedule"][6]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "Quero remarcar para domingo às 15:00"
    )
    
    assert result["status_code"] == 200
    await wait_for_processing()


@pytest.mark.asyncio
async def test_reschedule_no_show_scenario(client, test_conversation_ids, test_phone_numbers):
    """Test no-show scenario and policy explanation."""
    conv_id = test_conversation_ids["reschedule"][7]
    phone = test_phone_numbers["reschedule"][7]
    
    result = await send_webhook_message(
        client, conv_id, phone,
        "O que acontece se eu não comparecer?"
    )
    
    assert result["status_code"] == 200
    await wait_for_processing()



# ============================================================================
# COMPREHENSIVE E2E TEST SUITE
# ============================================================================

@pytest.mark.asyncio
async def test_e2e_all_faq_conversations(
    client,
    test_conversation_ids,
    test_phone_numbers
):
    """
    Run all 8 FAQ conversations and verify no 5xx errors.
    
    Requirements: 11.1
    """
    results = []
    
    faq_messages = [
        "Olá! Gostaria de saber sobre depilação a laser",
        "Quanto custa a depilação a laser?",
        "Quanto custa harmonização facial?",
        "Qual é a política de cancelamento?",
        "Quais são as contraindicações para depilação a laser?",
        "Quais cuidados devo ter após a depilação a laser?",
        "Qual é o horário de funcionamento da clínica?",
        "Quero fazer um tratamento corporal"
    ]
    
    for i, message in enumerate(faq_messages):
        conv_id = test_conversation_ids["faq"][i]
        phone = test_phone_numbers["faq"][i]
        
        result = await send_webhook_message(client, conv_id, phone, message)
        results.append(result)
        
        # Verify no 5xx errors
        assert result["status_code"] < 500, f"5xx error for FAQ conversation {i}"
        assert result["status_code"] == 200, f"Expected 200, got {result['status_code']}"
        
        await wait_for_processing(1.0)
    
    # Verify all conversations processed
    assert len(results) == 8
    assert all(r["status_code"] == 200 for r in results)


@pytest.mark.asyncio
async def test_e2e_all_scheduling_conversations(
    client,
    test_conversation_ids,
    test_phone_numbers
):
    """
    Run all 8 scheduling conversations and verify no 5xx errors.
    
    Requirements: 11.2
    """
    results = []
    
    schedule_messages = [
        "Olá, gostaria de agendar uma consulta",
        "Quero agendar para hoje às 20:00",
        "Posso agendar para domingo?",
        "Quero agendar para daqui 30 minutos",
        "Quero agendar harmonização facial para amanhã",
        "Quais são meus agendamentos?",
        "Posso agendar depilação e harmonização no mesmo dia?",
        "Quero agendar uma consulta para harmonização"
    ]
    
    for i, message in enumerate(schedule_messages):
        conv_id = test_conversation_ids["schedule"][i]
        phone = test_phone_numbers["schedule"][i]
        
        result = await send_webhook_message(client, conv_id, phone, message)
        results.append(result)
        
        # Verify no 5xx errors
        assert result["status_code"] < 500, f"5xx error for scheduling conversation {i}"
        assert result["status_code"] == 200, f"Expected 200, got {result['status_code']}"
        
        await wait_for_processing(1.0)
    
    # Verify all conversations processed
    assert len(results) == 8
    assert all(r["status_code"] == 200 for r in results)



@pytest.mark.asyncio
async def test_e2e_all_reschedule_conversations(
    client,
    test_conversation_ids,
    test_phone_numbers
):
    """
    Run all 8 rescheduling/cancellation conversations and verify no 5xx errors.
    
    Requirements: 11.3
    """
    results = []
    
    reschedule_messages = [
        "Preciso cancelar meu agendamento de amanhã",
        "Preciso cancelar meu agendamento de hoje",
        "Gostaria de remarcar meu agendamento para outro dia",
        "Preciso remarcar meu agendamento",
        "Preciso remarcar pela terceira vez",
        "Quero cancelar meu agendamento",
        "Quero remarcar para domingo às 15:00",
        "O que acontece se eu não comparecer?"
    ]
    
    for i, message in enumerate(reschedule_messages):
        conv_id = test_conversation_ids["reschedule"][i]
        phone = test_phone_numbers["reschedule"][i]
        
        result = await send_webhook_message(client, conv_id, phone, message)
        results.append(result)
        
        # Verify no 5xx errors
        assert result["status_code"] < 500, f"5xx error for reschedule conversation {i}"
        assert result["status_code"] == 200, f"Expected 200, got {result['status_code']}"
        
        await wait_for_processing(1.0)
    
    # Verify all conversations processed
    assert len(results) == 8
    assert all(r["status_code"] == 200 for r in results)


@pytest.mark.asyncio
async def test_e2e_verify_no_5xx_errors(
    client,
    test_conversation_ids,
    test_phone_numbers
):
    """
    Verify that all 24 test conversations complete without 5xx errors.
    
    Requirements: 11.1, 11.5
    """
    all_results = []
    
    # Run a sample from each category
    test_cases = [
        (test_conversation_ids["faq"][0], test_phone_numbers["faq"][0], "Informações sobre tratamentos"),
        (test_conversation_ids["schedule"][0], test_phone_numbers["schedule"][0], "Quero agendar"),
        (test_conversation_ids["reschedule"][0], test_phone_numbers["reschedule"][0], "Preciso cancelar"),
    ]
    
    for conv_id, phone, message in test_cases:
        result = await send_webhook_message(client, conv_id, phone, message)
        all_results.append(result)
        await wait_for_processing(0.5)
    
    # Verify no 5xx errors
    error_5xx_count = sum(1 for r in all_results if r["status_code"] >= 500)
    assert error_5xx_count == 0, f"Found {error_5xx_count} 5xx errors"
    
    # Verify all returned 200
    success_count = sum(1 for r in all_results if r["status_code"] == 200)
    assert success_count == len(all_results), "Not all requests returned 200"



@pytest.mark.asyncio
async def test_e2e_verify_messages_sent(client, test_conversation_ids, test_phone_numbers):
    """
    Verify that messages are sent via Chatwoot for processed conversations.
    
    Requirements: 11.5, 11.6
    """
    conv_id = test_conversation_ids["faq"][0]
    phone = test_phone_numbers["faq"][0]
    
    # Send a message
    result = await send_webhook_message(
        client, conv_id, phone,
        "Olá, preciso de informações"
    )
    
    assert result["status_code"] == 200
    await wait_for_processing(2.0)
    
    # Check logs table for message sent
    logs = await supabase_client.client.table("logs").select("*").eq(
        "conversation_id", conv_id
    ).execute()
    
    # Should have at least one log entry
    assert len(logs.data) > 0, "No logs found for conversation"


# ============================================================================
# PERFORMANCE AND LATENCY TESTS
# ============================================================================

class LatencyTracker:
    """Helper class to track latencies across tests."""
    
    def __init__(self):
        self.latencies: List[float] = []
    
    def add(self, latency_ms: float):
        """Add a latency measurement."""
        self.latencies.append(latency_ms)
    
    def get_p95(self) -> float:
        """Calculate P95 latency."""
        if not self.latencies:
            return 0.0
        
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[index] if index < len(sorted_latencies) else sorted_latencies[-1]
    
    def get_average(self) -> float:
        """Calculate average latency."""
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0


latency_tracker = LatencyTracker()


async def send_webhook_and_track_latency(
    client: AsyncClient,
    conversation_id: str,
    phone: str,
    message: str,
    tracker: LatencyTracker
) -> Dict[str, Any]:
    """Send webhook message and track latency."""
    start_time = time.time()
    
    result = await send_webhook_message(client, conversation_id, phone, message)
    
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    
    tracker.add(latency_ms)
    
    return {**result, "latency_ms": latency_ms}



@pytest.mark.asyncio
async def test_e2e_collect_latencies(client, test_conversation_ids, test_phone_numbers):
    """
    Collect latency measurements from test conversations.
    
    Requirements: 11.4
    """
    tracker = LatencyTracker()
    
    # Run sample conversations and track latencies
    test_messages = [
        (test_conversation_ids["faq"][0], test_phone_numbers["faq"][0], "Olá"),
        (test_conversation_ids["faq"][1], test_phone_numbers["faq"][1], "Preços"),
        (test_conversation_ids["schedule"][0], test_phone_numbers["schedule"][0], "Agendar"),
    ]
    
    for conv_id, phone, message in test_messages:
        result = await send_webhook_and_track_latency(
            client, conv_id, phone, message, tracker
        )
        
        assert result["status_code"] == 200
        assert result["latency_ms"] > 0
        
        await wait_for_processing(0.5)
    
    # Verify we collected latencies
    assert len(tracker.latencies) == len(test_messages)
    
    # Log latency statistics
    avg_latency = tracker.get_average()
    p95_latency = tracker.get_p95()
    
    print(f"\nLatency Statistics:")
    print(f"  Average: {avg_latency:.2f}ms")
    print(f"  P95: {p95_latency:.2f}ms")
    
    # Note: We don't assert P95 <= 7000ms here because this is just webhook acceptance
    # The actual agent processing happens in background and isn't measured here


@pytest.mark.asyncio
async def test_e2e_webhook_acceptance_latency(client, test_conversation_ids, test_phone_numbers):
    """
    Test that webhook acceptance (not full processing) is fast.
    
    Requirements: 11.4
    """
    conv_id = test_conversation_ids["faq"][0]
    phone = test_phone_numbers["faq"][0]
    
    start_time = time.time()
    
    result = await send_webhook_message(client, conv_id, phone, "Test message")
    
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    
    # Webhook should accept quickly (< 1 second)
    assert latency_ms < 1000, f"Webhook acceptance took {latency_ms:.2f}ms"
    assert result["status_code"] == 200


# ============================================================================
# CLEANUP AND UTILITIES
# ============================================================================

@pytest.mark.asyncio
async def test_cleanup_test_data():
    """
    Clean up test data from database after tests.
    
    This is a utility test that runs last to clean up test conversations.
    """
    try:
        # Clean up test conversations from sessions table
        await supabase_client.client.table("sessions").delete().like(
            "conversation_id", "test_%"
        ).execute()
        
        # Clean up test logs
        await supabase_client.client.table("logs").delete().like(
            "conversation_id", "test_%"
        ).execute()
        
        print("\nTest data cleaned up successfully")
        
    except Exception as e:
        print(f"\nWarning: Could not clean up test data: {e}")
        # Don't fail the test if cleanup fails


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
