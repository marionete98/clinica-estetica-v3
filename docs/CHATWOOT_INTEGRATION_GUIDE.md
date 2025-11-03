# Chatwoot Integration Guide

## Overview

This guide provides step-by-step instructions for configuring the Chatwoot webhook integration with the Clínica Luana Multi-Agent System. The integration enables the system to receive WhatsApp messages via Chatwoot and respond automatically through the AI agents.

**Requirements:** 1.1

## Architecture Overview

```
WhatsApp User → Chatwoot → Webhook → FastAPI Gateway → Agents → Response → Chatwoot → WhatsApp User
```

**Flow:**
1. Patient sends WhatsApp message
2. Chatwoot receives message and triggers webhook
3. **Deduplication check** (5-minute window)
4. **Message batching** (7-second delay for rapid messages)
5. Our system processes message with AI agents
6. System sends response back via Chatwoot API
7. Chatwoot delivers response to patient via WhatsApp

**Note:** The system implements intelligent message deduplication and batching. See [Message Deduplication and Batching Guide](MESSAGE_DEDUPLICATION_AND_BATCHING.md) for technical details.

## Prerequisites

Before configuring the webhook, ensure you have:

- [ ] Railway deployment URL (e.g., `https://your-app.railway.app`)
- [ ] Chatwoot account with admin access
- [ ] `CHATWOOT_WEBHOOK_SECRET` value from your environment variables
- [ ] System deployed and health check passing (`/health` returns 200)

## Step 1: Configure Webhook in Chatwoot

### 1.1 Access Webhook Settings

1. Log in to your Chatwoot account
2. Navigate to **Settings** (gear icon in sidebar)
3. Click on **Integrations** in the left menu
4. Select **Webhooks**
5. Click **Add Webhook** button

### 1.2 Configure Webhook Details

Fill in the webhook configuration form:

**Webhook URL:**
```
https://your-app.railway.app/webhook/chatwoot
```
Replace `your-app.railway.app` with your actual Railway deployment URL.

**Events to Subscribe:**
- ✅ `message_created` - **REQUIRED**
- ❌ Uncheck all other events

**Webhook Secret:**
Enter the value of your `CHATWOOT_WEBHOOK_SECRET` environment variable.

**Example:**
```
webhook_secret_abc123xyz789
```

⚠️ **Important:** The secret must match exactly with the value in your Railway environment variables.

### 1.3 Save Configuration

1. Click **Save** or **Create Webhook**
2. Verify the webhook appears in the list with status "Active"
3. Note the webhook ID for reference

## Step 2: Verify Webhook Configuration

### 2.1 Check Webhook Status

In Chatwoot:
1. Go to Settings → Integrations → Webhooks
2. Find your webhook in the list
3. Verify:
   - ✅ Status: Active
   - ✅ URL: Correct Railway URL
   - ✅ Events: `message_created` only

### 2.2 Test Webhook Endpoint

Test the endpoint is accessible:

```bash
curl -X POST https://your-app.railway.app/webhook/chatwoot \
  -H "Content-Type: application/json" \
  -H "X-Chatwoot-Signature: test" \
  -d '{
    "event": "message_created",
    "message_type": "incoming",
    "content": "test",
    "conversation": {"id": 123},
    "sender": {"phone_number": "+5594991398585"},
    "id": 1,
    "created_at": 1234567890
  }'
```

**Expected Response:**
```json
{
  "status": "accepted",
  "conversation_id": "123",
  "message": "Message queued for processing"
}
```

⚠️ **Note:** This test will fail signature validation but should return 401, not 404 or 500.

## Step 3: Configure Message Filters (Optional)

To ensure only relevant messages trigger the webhook:

### 3.1 Filter by Message Type

The webhook endpoint automatically filters:
- ✅ Accepts: `message_type == "incoming"`
- ❌ Rejects: `message_type == "outgoing"` (bot responses)
- ❌ Rejects: `message_type == "activity"` (system messages)

### 3.2 Filter by Conversation Status

In Chatwoot settings, you can optionally configure:
- Only trigger for "Open" conversations
- Skip "Resolved" or "Pending" conversations

**Recommendation:** Leave this open to allow patients to reopen conversations.

## Step 4: Run Automated Integration Tests

### 4.1 Use Test Script

Run the automated integration test script:

```bash
# Test deployed system
python scripts/test_chatwoot_integration.py https://your-app.railway.app

# Test local development
python scripts/test_chatwoot_integration.py http://localhost:8000
```

**What the script tests:**
- ✅ System health check
- ✅ Webhook signature generation
- ✅ Webhook payload validation
- ✅ Message processing
- ✅ Log creation in Supabase
- ✅ Multiple conversation scenarios

**Expected Output:**
```
==============================================================
CHATWOOT INTEGRATION TEST
==============================================================
Deployment URL: https://your-app.railway.app
Test Phone: +5594991398585
Test Conversation ID: 999999
==============================================================

PRE-CHECK: Health Endpoint
✅ System is healthy

Test Message 1/3
📤 Sending: Olá, gostaria de informações sobre depilação a laser
✅ Webhook accepted
✅ Log entry found!

Test Message 2/3
📤 Sending: Quais são os horários de funcionamento?
✅ Webhook accepted
✅ Log entry found!

Test Message 3/3
📤 Sending: Quero agendar uma consulta
✅ Webhook accepted
✅ Log entry found!

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

**Troubleshooting Test Failures:**
- If health check fails: Verify deployment is running
- If webhook fails: Check `CHATWOOT_WEBHOOK_SECRET` is set
- If logs not found: Check Supabase connection and permissions

### 4.2 Review Test Results

The test script validates:
1. **Health Check** - System is operational
2. **Webhook Acceptance** - Endpoint receives and validates payloads
3. **Message Processing** - Background processing completes
4. **Log Creation** - Supabase logs are created with correct data

If all tests pass, proceed to manual testing in Chatwoot.

## Step 5: Test Manual Flow in Chatwoot

### 5.1 Send Test Message via Chatwoot

1. Open Chatwoot dashboard
2. Go to **Conversations**
3. Select or create a test conversation
4. Send a test message as if you were a patient:
   ```
   Olá, gostaria de agendar uma consulta
   ```

### 5.2 Monitor Railway Logs

Watch the Railway logs for processing:

```bash
railway logs --tail
```

**Expected Log Sequence:**
```
INFO: Received webhook from Chatwoot
INFO: Processing message from conversation 123
INFO: Supervisor Agent routing to Scheduler Agent
INFO: Scheduler Agent processing booking request
INFO: Sending response via Chatwoot API
INFO: Message processed successfully
```

### 5.3 Verify Response in Chatwoot

1. Check the conversation in Chatwoot
2. Verify the bot responded with appropriate message
3. Check response time (should be < 7 seconds)

### 5.4 Verify Logs in Supabase

1. Open Supabase dashboard
2. Go to Table Editor → `logs` table
3. Find the most recent entry
4. Verify fields:
   - `conversation_id`: Matches Chatwoot conversation
   - `intent`: Detected intent (e.g., "schedule")
   - `provider`: LLM provider used
   - `latency_ms`: Response time
   - `error_message`: Should be NULL

## Step 6: Test Real WhatsApp Flow

### 6.1 Connect WhatsApp to Chatwoot

Ensure your Chatwoot account has WhatsApp connected:
1. Go to Settings → Inboxes
2. Verify WhatsApp inbox is configured
3. Note the WhatsApp number

### 6.2 Send Real WhatsApp Message

1. Use your personal phone
2. Send WhatsApp message to clinic number
3. Message should appear in Chatwoot
4. Bot should respond automatically

**Test Message Examples:**
```
Olá
Quero agendar depilação a laser
Quanto custa harmonização facial?
Quais são os horários de funcionamento?
```

### 6.3 Verify Complete Flow

Check each step:
- ✅ Message appears in Chatwoot
- ✅ Webhook triggered (check Railway logs)
- ✅ Agent processed message
- ✅ Response sent back to Chatwoot
- ✅ Response delivered to WhatsApp
- ✅ Log entry created in Supabase

## Troubleshooting

### Issue: Webhook Not Triggering

**Symptoms:** No logs in Railway when sending messages

**Checks:**
1. Verify webhook URL is correct in Chatwoot
2. Check webhook status is "Active"
3. Verify `message_created` event is selected
4. Check Railway service is running (`/health` returns 200)

**Solution:**
```bash
# Test health endpoint
curl https://your-app.railway.app/health

# Check Railway logs
railway logs --tail

# Verify webhook configuration in Chatwoot
```

### Issue: 401 Unauthorized Error

**Symptoms:** Webhook triggers but returns 401

**Cause:** Webhook signature validation failed

**Solution:**
1. Verify `CHATWOOT_WEBHOOK_SECRET` in Railway matches Chatwoot
2. Check for extra spaces or special characters
3. Update environment variable in Railway:
   ```bash
   railway variables set CHATWOOT_WEBHOOK_SECRET="your-secret-here"
   ```
4. Redeploy service

### Issue: 400 Bad Request Error

**Symptoms:** Webhook triggers but returns 400

**Cause:** Invalid payload structure

**Solution:**
1. Check Chatwoot webhook logs for payload format
2. Verify payload includes required fields:
   - `event`
   - `conversation`
   - `message_type`
   - `content`
   - `sender`
3. Check Railway logs for validation errors

### Issue: Bot Not Responding

**Symptoms:** Webhook succeeds but no response in Chatwoot

**Checks:**
1. Check Railway logs for agent processing errors
2. Verify LLM provider API key is valid
3. Check Chatwoot API credentials
4. Verify `CHATWOOT_API_TOKEN` is set correctly

**Solution:**
```bash
# Validate environment variables
python scripts/validate_env.py

# Check agent orchestrator logs
railway logs --filter "agent_orchestrator"

# Test Chatwoot API manually
curl -X POST https://app.chatwoot.com/api/v1/accounts/{account_id}/conversations/{conv_id}/messages \
  -H "api_access_token: your-token" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test message", "message_type": "outgoing"}'
```

### Issue: High Latency (> 7 seconds)

**Symptoms:** Responses take too long

**Checks:**
1. Check LLM provider status
2. Verify Redis connection
3. Check Supabase query performance
4. Review agent complexity

**Solution:**
1. Monitor metrics dashboard: `/dashboard`
2. Check P95 latency metric
3. Consider switching LLM provider if one is slow
4. Review agent prompts for optimization

### Issue: Duplicate Messages

**Symptoms:** Bot responds multiple times to same message

**Cause:** Webhook retries or race conditions

**Built-in Protection:**
The system automatically prevents duplicate processing with:
- 5-minute deduplication window
- Message ID tracking
- Automatic cleanup of old entries

**If duplicates still occur:**
1. Check for duplicate webhook configurations in Chatwoot
2. Verify message IDs are unique
3. Check Railway logs for deduplication events
4. Review `_processed_messages` cache size

**See:** [Message Deduplication and Batching Guide](MESSAGE_DEDUPLICATION_AND_BATCHING.md)

### Issue: Slow Response to Rapid Messages

**Symptoms:** User sends multiple messages but bot waits before responding

**Expected Behavior:**
The system batches rapid messages (7-second delay) to:
- Understand complete context
- Reduce LLM API calls
- Provide better responses

**Example:**
```
User: "Olá"           (10:00:00)
User: "Quero agendar" (10:00:03)
User: "Laser"         (10:00:05)
Bot: [Response]       (10:00:07) ← Processes all 3 together
```

**If delay is too long:**
1. Check `MESSAGE_PROCESSING_DELAY_SECONDS` setting (default: 7)
2. Monitor batch sizes in logs
3. Consider reducing delay for faster response
4. Balance between batching efficiency and response time

**See:** [Message Deduplication and Batching Guide](MESSAGE_DEDUPLICATION_AND_BATCHING.md)

## Webhook Payload Reference

### Example Incoming Message Payload

```json
{
  "event": "message_created",
  "id": 12345,
  "content": "Olá, gostaria de agendar uma consulta",
  "message_type": "incoming",
  "created_at": 1704672000,
  "conversation": {
    "id": 789,
    "inbox_id": 1,
    "status": "open"
  },
  "sender": {
    "id": 456,
    "name": "Maria Silva",
    "phone_number": "+5594991398585",
    "identifier": "+5594991398585",
    "type": "contact"
  },
  "account": {
    "id": 1,
    "name": "Clínica Luana"
  }
}
```

### Webhook Response Format

**Success (200 OK):**
```json
{
  "status": "accepted",
  "conversation_id": "789",
  "message": "Message queued for processing"
}
```

**Ignored (200 OK):**
```json
{
  "status": "ignored",
  "reason": "invalid_payload"
}
```

**Error (401 Unauthorized):**
```json
{
  "detail": "Invalid signature"
}
```

## Security Considerations

### Webhook Secret

- ✅ Use strong, random secret (min 32 characters)
- ✅ Store in environment variables, never in code
- ✅ Rotate secret every 90 days
- ✅ Use different secrets for staging/production

### Signature Validation

The webhook endpoint validates every request:
```python
def validate_chatwoot_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        CHATWOOT_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

### Rate Limiting

The webhook endpoint is rate-limited:
- **Limit:** 100 requests/minute per conversation_id
- **Response:** 429 Too Many Requests if exceeded
- **Purpose:** Prevent abuse and loops

## Monitoring

### Key Metrics to Monitor

1. **Webhook Success Rate**
   - Target: > 98%
   - Alert: < 95% for 10 minutes

2. **Response Latency**
   - Target: P95 < 7 seconds
   - Alert: P95 > 7 seconds for 10 minutes

3. **Error Rate**
   - Target: < 2%
   - Alert: > 2% for 10 minutes

### Monitoring Dashboard

Access the metrics dashboard:
```
https://your-app.railway.app/dashboard
```

**Metrics Displayed:**
- P95 Latency
- Handover Rate
- Conversion Rate
- Cost per Conversation
- Recent Errors

### Log Queries

**Find webhook errors:**
```sql
SELECT ts, conversation_id, error_message
FROM logs
WHERE error_message IS NOT NULL
  AND ts > NOW() - INTERVAL '1 hour'
ORDER BY ts DESC;
```

**Check webhook processing times:**
```sql
SELECT 
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency,
  AVG(latency_ms) as avg_latency,
  COUNT(*) as total_messages
FROM logs
WHERE ts > NOW() - INTERVAL '1 hour';
```

## Best Practices

### 1. Test in Staging First

- Set up separate Chatwoot webhook for staging
- Test all conversation flows
- Verify error handling
- Check performance under load

### 2. Monitor After Deployment

- Watch logs for first hour
- Check metrics dashboard every 15 minutes
- Review first 10 conversations manually
- Adjust prompts if needed

### 3. Handle Failures Gracefully

- System returns 200 OK even for invalid payloads
- Background processing prevents blocking
- Errors logged but don't stop service
- Escalation to human when stuck

### 4. Keep Webhook Configuration Simple

- Only subscribe to `message_created` event
- Don't add unnecessary filters
- Keep secret secure and rotated
- Document any changes

## Next Steps

After successful webhook configuration:

- [ ] Complete task 18.2: Test complete flow
- [ ] Run integration tests: `pytest tests/test_e2e.py`
- [ ] Verify all conversation types (FAQ, scheduling, cancellation)
- [ ] Monitor metrics for 24 hours
- [ ] Document any issues or improvements
- [ ] Train team on monitoring and troubleshooting

## Support

**Documentation:**
- Webhook Implementation: `routes/webhooks.py`
- Agent Orchestrator: `services/agent_orchestrator.py`
- Message Sender: `services/message_sender.py`

**Troubleshooting:**
- Error Handling Guide: `docs/ERROR_HANDLING_GUIDE.md`
- Deployment Guide: `docs/RAILWAY_DEPLOYMENT_GUIDE.md`
- Test Guide: `tests/E2E_TEST_GUIDE.md`

**External Resources:**
- Chatwoot Webhooks: https://www.chatwoot.com/docs/product/webhooks
- Railway Logs: https://docs.railway.app/develop/logs
- Supabase Dashboard: https://supabase.com/dashboard

---

**Requirements:** 1.1, 1.5, 3.5
