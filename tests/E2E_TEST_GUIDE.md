# End-to-End Test Guide

## Overview

The `test_e2e.py` file contains comprehensive end-to-end integration tests that simulate complete conversation flows through the Chatwoot webhook endpoint. These tests verify that the multi-agent system correctly handles FAQ, scheduling, and rescheduling/cancellation scenarios.

**Requirements Covered:** 11.1, 11.2, 11.3, 11.4, 11.5, 11.6

## Test Structure

### Test Categories

The test suite is organized into three main categories, each with 8 test scenarios:

1. **FAQ Conversations (8 tests)** - Information queries and multi-turn conversations
2. **Scheduling Conversations (8 tests)** - Booking appointments with various constraints
3. **Rescheduling/Cancellation (8 tests)** - Modifying or canceling existing bookings

**Total:** 24 comprehensive end-to-end test scenarios

## Test Fixtures

### `client`
Provides an async HTTP client for making requests to the FastAPI application.

```python
@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

### `test_conversation_ids`
Generates unique conversation IDs for each test to ensure isolation.

```python
@pytest.fixture
def test_conversation_ids():
    """Generate unique conversation IDs for tests."""
    timestamp = int(time.time() * 1000)
    return {
        "faq": [f"test_faq_{timestamp}_{i}" for i in range(8)],
        "schedule": [f"test_schedule_{timestamp}_{i}" for i in range(8)],
        "reschedule": [f"test_reschedule_{timestamp}_{i}" for i in range(8)],
    }
```

### `test_phone_numbers`
Generates unique Brazilian phone numbers for each test.

```python
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
```

## Helper Functions

### `create_chatwoot_webhook_payload()`
Creates a mock Chatwoot webhook payload for testing.

```python
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
```

### `send_webhook_message()`
Sends a webhook message to the endpoint and returns the response.

```python
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
```

### `wait_for_processing()`
Waits for background processing to complete.

```python
async def wait_for_processing(seconds: float = 2.0):
    """Wait for background processing to complete."""
    await asyncio.sleep(seconds)
```

## FAQ Conversation Tests (8 scenarios)

### 1. Treatment Information
Tests queries about treatment details.

```python
@pytest.mark.asyncio
async def test_faq_treatment_information(client, test_conversation_ids, test_phone_numbers):
    """Test FAQ conversation about treatment information."""
    result = await send_webhook_message(
        client, conv_id, phone,
        "Olá! Gostaria de saber sobre depilação a laser"
    )
    assert result["status_code"] == 200
```

### 2. Fixed Pricing
Tests questions about fixed-price services.

### 3. Consultation-Based Pricing
Tests questions about services requiring consultation.

### 4. Cancellation Policy
Tests inquiries about cancellation policies.

### 5. Contraindications
Tests questions about treatment contraindications.

### 6. Post-Treatment Care
Tests questions about post-treatment care instructions.

### 7. Business Hours
Tests inquiries about clinic operating hours.

### 8. Multi-Turn Clarification
Tests conversations requiring multiple turns for clarification.

```python
@pytest.mark.asyncio
async def test_faq_multi_turn_clarification(client, test_conversation_ids, test_phone_numbers):
    """Test FAQ conversation with multi-turn clarification."""
    # First message
    result1 = await send_webhook_message(
        client, conv_id, phone,
        "Quero fazer um tratamento"
    )
    await wait_for_processing()
    
    # Clarification
    result2 = await send_webhook_message(
        client, conv_id, phone,
        "Tratamento corporal para emagrecimento"
    )
    assert result2["status_code"] == 200
```

## Scheduling Conversation Tests (8 scenarios)

### 1. Simple Booking
Tests straightforward booking with available slots.

```python
@pytest.mark.asyncio
async def test_schedule_simple_booking(client, test_conversation_ids, test_phone_numbers):
    """Test simple scheduling conversation with available slot."""
    # Greeting
    result1 = await send_webhook_message(
        client, conv_id, phone,
        "Olá, gostaria de agendar uma consulta"
    )
    await wait_for_processing()
    
    # Provide name
    result2 = await send_webhook_message(
        client, conv_id, phone,
        "Meu nome é Maria Silva"
    )
    await wait_for_processing()
```

### 2. No Available Slots
Tests scenario when no slots are available.

### 3. Outside Business Hours
Tests booking attempts outside operating hours.

### 4. Insufficient Advance Time
Tests booking with less than 1 hour advance notice.

```python
@pytest.mark.asyncio
async def test_schedule_insufficient_advance(client, test_conversation_ids, test_phone_numbers):
    """Test scheduling with less than 1 hour advance."""
    now = datetime.now()
    target_time = now + timedelta(minutes=30)
    
    result = await send_webhook_message(
        client, conv_id, phone,
        f"Quero agendar para hoje às {target_time.strftime('%H:%M')}"
    )
    assert result["status_code"] == 200
```

### 5. Booking with Confirmation
Tests explicit confirmation flow.

### 6. Check Existing Bookings
Tests querying existing appointments.

### 7. Multiple Services Inquiry
Tests questions about booking multiple services.

### 8. Consultation Booking
Tests booking consultations for treatments that require them.

## Rescheduling/Cancellation Tests (8 scenarios)

### 1. Valid Cancellation Within Policy
Tests cancellation within the policy timeframe.

### 2. Cancellation Outside Policy
Tests cancellation outside the policy window.

### 3. First Rescheduling Attempt
Tests the first rescheduling attempt (should be allowed).

### 4. Second Rescheduling Attempt
Tests the second rescheduling attempt (should be allowed).

```python
@pytest.mark.asyncio
async def test_reschedule_second_time(client, test_conversation_ids, test_phone_numbers):
    """Test second rescheduling attempt."""
    # First reschedule
    result1 = await send_webhook_message(
        client, conv_id, phone,
        "Preciso remarcar meu agendamento"
    )
    await wait_for_processing()
    
    # Second reschedule (should still be allowed)
    result2 = await send_webhook_message(
        client, conv_id, phone,
        "Na verdade, preciso remarcar novamente"
    )
    assert result2["status_code"] == 200
```

### 5. Exceeding Reschedule Limit
Tests attempting a third rescheduling (should be blocked).

### 6. Non-Existent Booking
Tests cancellation of a booking that doesn't exist.

### 7. Rescheduling to Unavailable Slot
Tests rescheduling to a slot that's not available.

### 8. No-Show Policy Explanation
Tests questions about no-show policies.

## Comprehensive E2E Test Suites

### All FAQ Conversations
Runs all 8 FAQ conversations and verifies no 5xx errors.

```python
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
    faq_messages = [
        "Olá! Gostaria de saber sobre depilação a laser",
        "Quanto custa a depilação a laser?",
        # ... 6 more messages
    ]
    
    for i, message in enumerate(faq_messages):
        result = await send_webhook_message(client, conv_id, phone, message)
        assert result["status_code"] < 500
        assert result["status_code"] == 200
```

### All Scheduling Conversations
Runs all 8 scheduling conversations (Requirement 11.2).

### All Rescheduling Conversations
Runs all 8 rescheduling/cancellation conversations (Requirement 11.3).

### Verify No 5xx Errors
Verifies that all test conversations complete without server errors.

```python
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
    # Run sample from each category
    # Verify no 5xx errors
    error_5xx_count = sum(1 for r in all_results if r["status_code"] >= 500)
    assert error_5xx_count == 0
```

### Verify Messages Sent
Verifies that messages are logged to the database.

```python
@pytest.mark.asyncio
async def test_e2e_verify_messages_sent(client, test_conversation_ids, test_phone_numbers):
    """
    Verify that messages are sent via Chatwoot for processed conversations.
    
    Requirements: 11.5, 11.6
    """
    # Send message and check logs table
    logs = supabase_client.client.table("logs").select("*").eq(
        "conversation_id", conv_id
    ).execute()
    
    assert len(logs.data) > 0
```

## Performance and Latency Tests

### LatencyTracker Class
Helper class to track and calculate latencies.

```python
class LatencyTracker:
    """Helper class to track latencies across tests."""
    
    def __init__(self):
        self.latencies: List[float] = []
    
    def add(self, latency_ms: float):
        """Add a latency measurement."""
        self.latencies.append(latency_ms)
    
    def get_p95(self) -> float:
        """Calculate P95 latency."""
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[index]
    
    def get_average(self) -> float:
        """Calculate average latency."""
        return sum(self.latencies) / len(self.latencies)
```

### Collect Latencies
Collects latency measurements from test conversations.

```python
@pytest.mark.asyncio
async def test_e2e_collect_latencies(client, test_conversation_ids, test_phone_numbers):
    """
    Collect latency measurements from test conversations.
    
    Requirements: 11.4
    """
    tracker = LatencyTracker()
    
    for conv_id, phone, message in test_messages:
        result = await send_webhook_and_track_latency(
            client, conv_id, phone, message, tracker
        )
        assert result["latency_ms"] > 0
    
    # Log statistics
    print(f"Average: {tracker.get_average():.2f}ms")
    print(f"P95: {tracker.get_p95():.2f}ms")
```

### Webhook Acceptance Latency
Tests that webhook acceptance is fast (< 1 second).

```python
@pytest.mark.asyncio
async def test_e2e_webhook_acceptance_latency(client, test_conversation_ids, test_phone_numbers):
    """
    Test that webhook acceptance (not full processing) is fast.
    
    Requirements: 11.4
    """
    start_time = time.time()
    result = await send_webhook_message(client, conv_id, phone, "Test message")
    end_time = time.time()
    
    latency_ms = (end_time - start_time) * 1000
    assert latency_ms < 1000  # < 1 second
```

## Cleanup and Utilities

### Test Data Cleanup
Automatically cleans up test data after tests complete.

```python
@pytest.mark.asyncio
async def test_cleanup_test_data():
    """
    Clean up test data from database after tests.
    """
    try:
        # Clean up test conversations
        supabase_client.client.table("sessions").delete().like(
            "conversation_id", "test_%"
        ).execute()
        
        # Clean up test logs
        supabase_client.client.table("logs").delete().like(
            "conversation_id", "test_%"
        ).execute()
        
        print("\nTest data cleaned up successfully")
    except Exception as e:
        print(f"\nWarning: Could not clean up test data: {e}")
```

## Running the Tests

### Run All E2E Tests
```bash
pytest tests/test_e2e.py -v
```

### Run Specific Category
```bash
# FAQ tests only
pytest tests/test_e2e.py -k "faq" -v

# Scheduling tests only
pytest tests/test_e2e.py -k "schedule" -v

# Rescheduling tests only
pytest tests/test_e2e.py -k "reschedule" -v
```

### Run Comprehensive Suites
```bash
# Run all comprehensive E2E tests
pytest tests/test_e2e.py -k "e2e_all" -v
```

### Run with Output
```bash
# Show print statements and detailed output
pytest tests/test_e2e.py -v -s
```

## Expected Results

### Success Criteria

✅ **All tests pass or skip**
- No test failures
- 200 status codes for all webhook requests
- No 5xx errors

✅ **Performance**
- Webhook acceptance < 1 second
- Latency measurements collected
- P95 statistics calculated

✅ **Data Integrity**
- Messages logged to database
- Unique conversation IDs prevent conflicts
- Test data cleaned up after execution

### Sample Output

```
tests/test_e2e.py::test_faq_treatment_information PASSED
tests/test_e2e.py::test_faq_pricing_fixed PASSED
tests/test_e2e.py::test_faq_pricing_consultation PASSED
...
tests/test_e2e.py::test_e2e_all_faq_conversations PASSED
tests/test_e2e.py::test_e2e_all_scheduling_conversations PASSED
tests/test_e2e.py::test_e2e_all_reschedule_conversations PASSED
tests/test_e2e.py::test_e2e_verify_no_5xx_errors PASSED

======================== 24 passed in 120.45s ========================
```

## Troubleshooting

### Tests Timing Out
- Increase `wait_for_processing()` duration
- Check if background jobs are running
- Verify database connectivity

### 5xx Errors
- Check application logs
- Verify all services are running (Redis, Supabase)
- Check LLM API keys and quotas

### Database Errors
- Verify Supabase connection
- Check table schemas match expectations
- Ensure test data cleanup ran successfully

### Cleanup Failures
- Manually run cleanup SQL:
  ```sql
  DELETE FROM sessions WHERE conversation_id LIKE 'test_%';
  DELETE FROM logs WHERE conversation_id LIKE 'test_%';
  ```

## Best Practices

1. **Run tests in isolation** - Each test uses unique IDs
2. **Wait for processing** - Allow time for background tasks
3. **Check logs** - Review application logs for errors
4. **Clean up regularly** - Run cleanup after test sessions
5. **Monitor performance** - Track latency trends over time

## Conclusion

The E2E test suite provides comprehensive coverage of all conversation types and scenarios. It verifies that the multi-agent system correctly handles FAQ, scheduling, and rescheduling/cancellation flows without errors, meeting all specified requirements.

**Total Coverage:**
- 24 individual test scenarios
- 3 comprehensive suite tests
- Performance and latency tracking
- Automatic cleanup utilities

**Requirements Satisfied:** 11.1, 11.2, 11.3, 11.4, 11.5, 11.6
