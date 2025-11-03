# Integration Tests - Clínica Luana Multi-Agent System

This directory contains comprehensive integration tests for the multi-agent scheduling system.

## Test Suites

### 1. End-to-End Tests (`test_e2e.py`)

Tests complete conversation flows through the webhook endpoint.

**Coverage:**
- 8 FAQ conversations (treatment info, pricing, policies, contraindications, etc.)
- 8 Scheduling conversations (simple booking, no slots, outside hours, etc.)
- 8 Rescheduling/Cancellation conversations (valid/invalid cancellation, reschedule limits, etc.)

**Requirements Tested:** 11.1, 11.2, 11.3, 11.4, 11.5, 11.6

**Key Tests:**
- `test_e2e_all_faq_conversations` - Runs all 8 FAQ scenarios
- `test_e2e_all_scheduling_conversations` - Runs all 8 scheduling scenarios
- `test_e2e_all_reschedule_conversations` - Runs all 8 reschedule scenarios
- `test_e2e_verify_no_5xx_errors` - Verifies no server errors
- `test_e2e_verify_messages_sent` - Verifies messages are logged

### 2. Performance Tests (`test_performance.py`)

Validates system performance and latency requirements.

**Coverage:**
- Webhook acceptance latency (< 1 second)
- P95 latency calculation from logs
- Health endpoint performance
- Metrics endpoint performance
- Concurrent webhook handling (10 concurrent requests)

**Requirements Tested:** 11.4

**Key Tests:**
- `test_webhook_acceptance_latency` - Measures webhook response time
- `test_calculate_p95_from_logs` - Validates P95 ≤ 7 seconds requirement
- `test_concurrent_webhook_handling` - Tests under load
- `test_performance_summary` - Generates comprehensive report

### 3. Error Scenario Tests (`test_error_scenarios.py`)

Tests graceful degradation when dependencies fail.

**Coverage:**
- Redis unavailable scenarios
- Supabase slow/down scenarios
- LLM timeout scenarios
- Multiple simultaneous failures
- Recovery after failures

**Requirements Tested:** 12.2, 12.3, 12.4

**Key Tests:**
- `test_redis_unavailable_graceful_degradation` - System operates without context
- `test_supabase_slow_response` - Handles slow database queries
- `test_llm_timeout_handling` - Handles LLM API timeouts
- `test_multiple_dependencies_failing` - Handles cascading failures
- `test_recovery_after_redis_failure` - Verifies recovery

## Running Tests

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Run All Integration Tests

```bash
# Using the test runner script
python tests/run_integration_tests.py

# Or using pytest directly
pytest tests/test_e2e.py tests/test_performance.py tests/test_error_scenarios.py -v
```

### Run Individual Test Suites

```bash
# E2E tests only
pytest tests/test_e2e.py -v

# Performance tests only
pytest tests/test_performance.py -v

# Error scenario tests only
pytest tests/test_error_scenarios.py -v
```

### Run Specific Tests

```bash
# Run a specific test function
pytest tests/test_e2e.py::test_faq_treatment_information -v

# Run tests matching a pattern
pytest tests/test_e2e.py -k "faq" -v
```

### Generate Coverage Report

```bash
pytest tests/ --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Configuration

### Environment Variables

Tests use the same environment variables as the main application:

```bash
# Required for tests
MODEL_PROVIDER=gemini  # or xai
GEMINI_API_KEY=your_key_here
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
REDIS_URL=redis://localhost:6379
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_ACCOUNT_ID=12345
CHATWOOT_API_TOKEN=your_token
CHATWOOT_WEBHOOK_SECRET=your_secret
```

### Test Database

Tests use the same Supabase instance as development. Test data is prefixed with `test_` and cleaned up after tests.

## Success Criteria

### E2E Tests
- ✓ 0 errors (5xx responses) across all 24 conversations
- ✓ All webhooks accepted (200 status)
- ✓ Bookings created in database (for scheduling tests)
- ✓ Messages logged to Supabase

### Performance Tests
- ✓ Webhook acceptance < 1 second
- ✓ P95 latency ≤ 7 seconds (end-to-end with agent processing)
- ✓ Health endpoint < 500ms
- ✓ Metrics endpoint < 2 seconds
- ✓ Handles 10 concurrent requests

### Error Scenario Tests
- ✓ System accepts webhooks when Redis is down
- ✓ System continues when Supabase is slow
- ✓ System handles LLM timeouts gracefully
- ✓ System recovers after failures
- ✓ No crashes or unhandled exceptions

## Test Data Cleanup

Tests automatically clean up test data:

```python
# Cleanup runs after tests
@pytest.mark.asyncio
async def test_cleanup_test_data():
    # Removes all test_* conversations and logs
    pass
```

Manual cleanup if needed:

```sql
-- Clean up test sessions
DELETE FROM sessions WHERE conversation_id LIKE 'test_%';

-- Clean up test logs
DELETE FROM logs WHERE conversation_id LIKE 'test_%';

-- Clean up test contacts
DELETE FROM contacts WHERE phone LIKE '+5594999%';
```

## Troubleshooting

### Tests Fail to Connect to Services

**Issue:** Connection errors to Redis, Supabase, or Chatwoot

**Solution:**
1. Verify environment variables are set correctly
2. Check that services are running and accessible
3. For local development, ensure Redis is running: `redis-server`

### LLM API Rate Limits

**Issue:** Tests fail due to rate limiting

**Solution:**
1. Add delays between tests: `await asyncio.sleep(1.0)`
2. Use test mode with mocked LLM responses
3. Run tests in smaller batches

### Database State Issues

**Issue:** Tests fail due to existing data

**Solution:**
1. Run cleanup: `pytest tests/test_e2e.py::test_cleanup_test_data`
2. Use unique test IDs with timestamps
3. Reset test database if needed

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run integration tests
        env:
          MODEL_PROVIDER: ${{ secrets.MODEL_PROVIDER }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          REDIS_URL: ${{ secrets.REDIS_URL }}
        run: pytest tests/ -v --tb=short
```

## Notes

- **Webhook Acceptance vs Full Processing:** Tests measure webhook acceptance time (< 1s), not full agent processing time. Full end-to-end latency (webhook → agent → response) is measured in production via logs.

- **Background Processing:** The webhook endpoint returns 200 immediately and processes messages in background. Tests verify acceptance, not completion.

- **Mock vs Real Services:** Most tests use real services (Supabase, Redis). Error scenario tests use mocks to simulate failures.

- **Test Isolation:** Each test uses unique conversation IDs and phone numbers to avoid conflicts.

## Contact

For questions about tests, see:
- Main documentation: `README.md`
- Agent guide: `docs/AGENTS_GUIDE.md`
- Error handling: `docs/ERROR_HANDLING_GUIDE.md`
