# Chatwoot Integration Test Script Guide

## Overview

The `test_chatwoot_integration.py` script provides automated testing for the complete Chatwoot webhook integration flow. It validates that webhooks are properly configured, messages are processed correctly, and logs are created in Supabase.

**Script Location:** `scripts/test_chatwoot_integration.py`

**Requirements:** 1.1, 1.5, 3.5

## What It Tests

The script performs comprehensive integration testing:

### 1. Pre-Flight Checks
- ✅ System health endpoint (`/health`)
- ✅ Service availability
- ✅ Basic connectivity

### 2. Webhook Processing
- ✅ HMAC SHA256 signature generation
- ✅ Webhook payload validation
- ✅ Webhook endpoint acceptance (200 OK)
- ✅ Proper payload structure

### 3. Message Processing
- ✅ Background message processing
- ✅ Agent orchestration
- ✅ Response generation
- ✅ Multiple conversation scenarios

### 4. Data Persistence
- ✅ Log creation in Supabase
- ✅ Correct conversation_id tracking
- ✅ Intent detection logging
- ✅ Latency measurement
- ✅ Error tracking

## Usage

### Basic Usage

```bash
# Test deployed system
python scripts/test_chatwoot_integration.py https://your-app.railway.app

# Test local development
python scripts/test_chatwoot_integration.py http://localhost:8000

# Test with default (localhost)
python scripts/test_chatwoot_integration.py
```

### Prerequisites

1. **Environment Variables:**
   ```bash
   CHATWOOT_WEBHOOK_SECRET=your-webhook-secret
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-service-role-key
   ```

2. **Dependencies:**
   ```bash
   pip install httpx python-dotenv
   ```

3. **System Requirements:**
   - Target system must be running
   - Webhook endpoint must be accessible
   - Supabase database must be configured

## Test Scenarios

The script tests three conversation scenarios:

### Scenario 1: FAQ Request
**Message:** "Olá, gostaria de informações sobre depilação a laser"

**Expected Flow:**
1. Webhook accepted
2. Supervisor routes to FAQ agent
3. FAQ agent provides treatment information
4. Log created with intent="faq"

### Scenario 2: Business Hours Inquiry
**Message:** "Quais são os horários de funcionamento?"

**Expected Flow:**
1. Webhook accepted
2. Supervisor routes to FAQ agent
3. FAQ agent provides business hours
4. Log created with intent="faq"

### Scenario 3: Scheduling Request
**Message:** "Quero agendar uma consulta"

**Expected Flow:**
1. Webhook accepted
2. Supervisor routes to Scheduler agent
3. Scheduler agent initiates booking flow
4. Log created with intent="schedule"

## Output Format

### Successful Test Run

```
==============================================================
CHATWOOT INTEGRATION TEST
==============================================================
Deployment URL: https://your-app.railway.app
Test Phone: +5594991398585
Test Conversation ID: 999999
==============================================================

==============================================================
PRE-CHECK: Health Endpoint
==============================================================
🏥 Checking health: https://your-app.railway.app/health
📥 Response Status: 200
📥 Response: {
  "status": "healthy",
  "redis": "connected",
  "supabase": "connected",
  "chatwoot": "connected"
}
✅ System is healthy

==============================================================
Test Message 1/3
==============================================================
📤 Sending: Olá, gostaria de informações sobre depilação a laser
📥 Status: 200
✅ Webhook accepted
⏱️  Waiting 5 seconds for processing...

==============================================================
TEST 2: Verify Logs in Supabase
==============================================================
🔍 Checking for logs with conversation_id: 1000000
⏱️  Waiting up to 15 seconds...
✅ Log entry found!
   - Timestamp: 2025-10-16T10:30:45.123Z
   - Intent: faq
   - Provider: xai
   - Latency: 3450ms
   - Error: None

[... similar output for messages 2 and 3 ...]

==============================================================
TEST SUMMARY
==============================================================
✅ PASS - Health Check
✅ PASS - Message 1 - Webhook
✅ PASS - Message 1 - Logs
✅ PASS - Message 2 - Webhook
✅ PASS - Message 2 - Logs
✅ PASS - Message 3 - Webhook
✅ PASS - Message 3 - Logs

==============================================================
Results: 7/7 tests passed
==============================================================

🎉 All tests passed!
```

### Failed Test Run

```
==============================================================
CHATWOOT INTEGRATION TEST
==============================================================
Deployment URL: https://your-app.railway.app
Test Phone: +5594991398585
Test Conversation ID: 999999
==============================================================

==============================================================
PRE-CHECK: Health Endpoint
==============================================================
🏥 Checking health: https://your-app.railway.app/health
❌ Error checking health: Connection refused

⚠️  System is not healthy, but continuing with tests...

==============================================================
Test Message 1/3
==============================================================
📤 Sending: Olá, gostaria de informações sobre depilação a laser
❌ Webhook failed: 500

==============================================================
TEST SUMMARY
==============================================================
✅ PASS - Health Check
❌ FAIL - Message 1 - Webhook
❌ FAIL - Message 1 - Logs
[...]

==============================================================
Results: 1/7 tests passed
==============================================================

⚠️  Some tests failed. Check the output above for details.
```

## Configuration

### Test Data

The script uses predefined test data:

```python
TEST_PHONE = "+5594991398585"
TEST_CONVERSATION_ID = 999999
TEST_MESSAGE_ID = 888888
```

Each test message uses a unique conversation ID:
- Message 1: 1000000
- Message 2: 1000001
- Message 3: 1000002

### Timeouts

```python
# HTTP request timeout
timeout = 30.0  # seconds

# Log verification timeout
log_timeout = 15  # seconds

# Processing wait time
processing_wait = 5  # seconds
```

### Signature Generation

The script generates HMAC SHA256 signatures:

```python
def generate_signature(payload: str, secret: str) -> str:
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
```

## Troubleshooting

### Test Fails: "CHATWOOT_WEBHOOK_SECRET not configured"

**Cause:** Environment variable not set

**Solution:**
```bash
# Set in .env file
echo "CHATWOOT_WEBHOOK_SECRET=your-secret-here" >> .env

# Or export directly
export CHATWOOT_WEBHOOK_SECRET=your-secret-here
```

### Test Fails: "Connection refused"

**Cause:** Target system not running or URL incorrect

**Solution:**
1. Verify deployment URL is correct
2. Check system is running: `curl https://your-app.railway.app/health`
3. Check Railway logs: `railway logs`
4. Verify network connectivity

### Test Fails: "Webhook failed with status 401"

**Cause:** Signature validation failed

**Solution:**
1. Verify `CHATWOOT_WEBHOOK_SECRET` matches Railway environment
2. Check for extra spaces or special characters
3. Update Railway environment variable
4. Redeploy service

### Test Fails: "No logs found after 15 seconds"

**Cause:** Message processing failed or Supabase connection issue

**Solution:**
1. Check Railway logs for processing errors
2. Verify Supabase credentials are correct
3. Check `logs` table exists in Supabase
4. Verify service_role key has write permissions
5. Increase timeout if system is slow

### Test Passes but No Response in Chatwoot

**Cause:** Test script only validates webhook acceptance, not Chatwoot API

**Solution:**
1. Check Railway logs for Chatwoot API errors
2. Verify `CHATWOOT_API_TOKEN` is set correctly
3. Test Chatwoot API manually
4. Check Chatwoot account permissions

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run Chatwoot integration tests
        env:
          CHATWOOT_WEBHOOK_SECRET: ${{ secrets.CHATWOOT_WEBHOOK_SECRET }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: |
          python scripts/test_chatwoot_integration.py ${{ secrets.DEPLOYMENT_URL }}
```

### Railway Deployment Hook

Add to `railway.json`:

```json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  },
  "hooks": {
    "postDeploy": "python scripts/test_chatwoot_integration.py $RAILWAY_PUBLIC_DOMAIN"
  }
}
```

## Best Practices

### 1. Run Before Production Deploy

Always run integration tests before deploying to production:

```bash
# Test staging
python scripts/test_chatwoot_integration.py https://staging.railway.app

# If all pass, deploy to production
railway up --environment production

# Test production
python scripts/test_chatwoot_integration.py https://production.railway.app
```

### 2. Monitor Test Results

Track test results over time:
- Log test runs to monitoring system
- Alert on test failures
- Review failed tests before deploying

### 3. Use in Development

Run tests during development:

```bash
# Start local server
uvicorn main:app --reload

# In another terminal, run tests
python scripts/test_chatwoot_integration.py http://localhost:8000
```

### 4. Customize for Your Environment

Modify test scenarios to match your use cases:

```python
test_messages = [
    "Your custom test message 1",
    "Your custom test message 2",
    "Your custom test message 3"
]
```

## Exit Codes

The script uses standard exit codes:

- **0**: All tests passed
- **1**: One or more tests failed

Use in scripts:

```bash
#!/bin/bash
python scripts/test_chatwoot_integration.py https://your-app.railway.app

if [ $? -eq 0 ]; then
    echo "Tests passed, deploying to production..."
    railway up --environment production
else
    echo "Tests failed, aborting deployment"
    exit 1
fi
```

## Related Documentation

- **Chatwoot Integration Guide:** `docs/CHATWOOT_INTEGRATION_GUIDE.md`
- **Webhook Implementation:** `routes/webhooks.py`
- **E2E Test Guide:** `tests/E2E_TEST_GUIDE.md`
- **Scripts README:** `scripts/README.md`

## Support

For issues with the test script:

1. Check script output for specific error messages
2. Verify environment variables are set correctly
3. Test endpoints manually with curl
4. Review Railway logs for processing errors
5. Check Supabase logs for database issues

---

**Last Updated:** 2025-10-16  
**Requirements:** 1.1, 1.5, 3.5
