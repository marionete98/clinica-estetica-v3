# Chatwoot Integration Checklist

## Task 18: Configurar Integrações Externas

This checklist guides you through configuring and testing the Chatwoot webhook integration.

**Requirements:** 1.1, 1.5, 3.5

---

## 18.1 Configurar Webhook no Chatwoot

### Prerequisites

- [ ] Railway deployment is live and accessible
- [ ] Health endpoint returns 200: `curl https://your-app.railway.app/health`
- [ ] All environment variables are configured in Railway
- [ ] `CHATWOOT_WEBHOOK_SECRET` is set and documented
- [ ] Chatwoot account has admin access

### Step 1: Get Deployment Information

- [ ] Note your Railway deployment URL: `https://_____.railway.app`
- [ ] Verify health endpoint works:
  ```bash
  curl https://your-app.railway.app/health
  ```
- [ ] Expected response: `{"status": "healthy", ...}`

### Step 2: Configure Webhook in Chatwoot

- [ ] Log in to Chatwoot account
- [ ] Navigate to: Settings → Integrations → Webhooks
- [ ] Click "Add Webhook" button
- [ ] Fill in webhook configuration:
  - [ ] **URL:** `https://your-app.railway.app/webhook/chatwoot`
  - [ ] **Events:** Select only `message_created` ✅
  - [ ] **Events:** Uncheck all other events ❌
  - [ ] **Secret:** Enter your `CHATWOOT_WEBHOOK_SECRET` value
- [ ] Click "Save" or "Create Webhook"
- [ ] Verify webhook appears in list with status "Active"

### Step 3: Verify Webhook Configuration

- [ ] Webhook status shows as "Active" in Chatwoot
- [ ] Webhook URL is correct (no typos)
- [ ] Only `message_created` event is selected
- [ ] Secret matches Railway environment variable exactly

### Step 4: Test Webhook Endpoint

- [ ] Test endpoint is accessible:
  ```bash
  curl -X POST https://your-app.railway.app/webhook/chatwoot \
    -H "Content-Type: application/json" \
    -d '{"event":"message_created","message_type":"incoming","content":"test","conversation":{"id":123},"sender":{"phone_number":"+5594991398585"},"id":1,"created_at":1234567890}'
  ```
- [ ] Response should be 200 or 401 (not 404 or 500)

### Step 5: Document Configuration

- [ ] Document webhook URL in team wiki/docs
- [ ] Document webhook secret location (Railway env vars)
- [ ] Document webhook ID from Chatwoot
- [ ] Add configuration to deployment checklist

### Completion Criteria for 18.1

- ✅ Webhook configured in Chatwoot
- ✅ Webhook status is "Active"
- ✅ Endpoint is accessible and returns valid response
- ✅ Configuration is documented

---

## 18.2 Testar Fluxo Completo via Chatwoot

### Prerequisites

- [ ] Task 18.1 completed successfully
- [ ] System is deployed and healthy
- [ ] Supabase database is accessible
- [ ] LLM provider API keys are valid

### Test 1: Send Test Message in Chatwoot

- [ ] Open Chatwoot dashboard
- [ ] Go to Conversations
- [ ] Create or select a test conversation
- [ ] Send test message: "Olá, gostaria de informações sobre depilação a laser"
- [ ] Wait up to 10 seconds for response

### Test 2: Verify Webhook Received

- [ ] Open Railway logs: `railway logs --tail`
- [ ] Look for log entry: "Received webhook from Chatwoot"
- [ ] Verify conversation ID matches Chatwoot
- [ ] No error messages in logs

**Expected Log Sequence:**
```
INFO: Received webhook from Chatwoot
INFO: Processing message from conversation 123
INFO: Supervisor Agent routing to FAQ Agent
INFO: FAQ Agent processing query
INFO: Sending response via Chatwoot API
INFO: Message processed successfully
```

### Test 3: Verify Response Sent via Chatwoot

- [ ] Check conversation in Chatwoot
- [ ] Bot response appears in conversation
- [ ] Response is relevant to the question
- [ ] Response time is reasonable (< 10 seconds)
- [ ] Message is marked as "outgoing" from bot

### Test 4: Verify Logs in Supabase

- [ ] Open Supabase dashboard
- [ ] Go to Table Editor → `logs` table
- [ ] Find most recent entry
- [ ] Verify fields:
  - [ ] `conversation_id`: Matches Chatwoot conversation
  - [ ] `intent`: Detected intent (e.g., "faq")
  - [ ] `provider`: LLM provider used (e.g., "gemini")
  - [ ] `latency_ms`: Response time in milliseconds
  - [ ] `error_message`: Should be NULL
  - [ ] `ts`: Recent timestamp

### Test 5: Run Automated Integration Test

- [ ] Run test script:
  ```bash
  python scripts/test_chatwoot_integration.py https://your-app.railway.app
  ```
- [ ] All tests pass ✅
- [ ] No errors in output
- [ ] Logs created in Supabase

### Test 6: Test Real WhatsApp Flow

**Note:** Only if WhatsApp is connected to Chatwoot

- [ ] Send WhatsApp message to clinic number from personal phone
- [ ] Message appears in Chatwoot
- [ ] Webhook triggers (check Railway logs)
- [ ] Bot responds automatically
- [ ] Response delivered to WhatsApp
- [ ] Response is appropriate and helpful

### Test 7: Test Different Message Types

Test each conversation type:

**FAQ Messages:**
- [ ] "Quais são os horários de funcionamento?"
- [ ] "Quanto custa harmonização facial?"
- [ ] "Quais tratamentos vocês oferecem?"

**Scheduling Messages:**
- [ ] "Quero agendar depilação a laser"
- [ ] "Tem horário disponível amanhã?"
- [ ] "Gostaria de marcar uma consulta"

**Cancellation Messages:**
- [ ] "Preciso cancelar meu agendamento"
- [ ] "Quero remarcar minha consulta"

**Greeting Messages:**
- [ ] "Olá"
- [ ] "Oi, tudo bem?"
- [ ] "Bom dia"

### Test 8: Verify Error Handling

- [ ] Send very long message (> 4000 chars)
  - [ ] System handles gracefully
  - [ ] Returns appropriate error or truncates
  
- [ ] Send message with special characters
  - [ ] System processes correctly
  - [ ] No encoding errors
  
- [ ] Send rapid messages (5 in 10 seconds)
  - [ ] All messages processed
  - [ ] No rate limit errors (under 100/min)

### Test 9: Verify Metrics and Monitoring

- [ ] Access dashboard: `https://your-app.railway.app/dashboard`
- [ ] Verify metrics are updating:
  - [ ] P95 Latency shows recent data
  - [ ] Handover Rate is calculated
  - [ ] Conversion Rate is tracked
  - [ ] Cost per Conversation is estimated
- [ ] Recent errors section shows any issues
- [ ] Metrics refresh automatically

### Test 10: End-to-End Flow Verification

Complete flow for one conversation:

- [ ] **Step 1:** Patient sends WhatsApp message
- [ ] **Step 2:** Message appears in Chatwoot
- [ ] **Step 3:** Chatwoot triggers webhook
- [ ] **Step 4:** Railway receives webhook (check logs)
- [ ] **Step 5:** Webhook signature validated
- [ ] **Step 6:** Message queued for processing
- [ ] **Step 7:** Agent orchestrator processes message
- [ ] **Step 8:** Appropriate agent handles request
- [ ] **Step 9:** Response generated by LLM
- [ ] **Step 10:** Response sent via Chatwoot API
- [ ] **Step 11:** Chatwoot delivers to WhatsApp
- [ ] **Step 12:** Log entry created in Supabase
- [ ] **Step 13:** Metrics updated in dashboard

### Completion Criteria for 18.2

- ✅ Test messages sent successfully
- ✅ Webhooks received and processed
- ✅ Responses sent back to Chatwoot
- ✅ Logs created in Supabase
- ✅ All conversation types tested
- ✅ Error handling verified
- ✅ Metrics dashboard working
- ✅ End-to-end flow complete

---

## Troubleshooting Guide

### Issue: Webhook Not Triggering

**Symptoms:** No logs in Railway when sending messages

**Debug Steps:**
1. [ ] Check webhook status in Chatwoot (should be "Active")
2. [ ] Verify webhook URL is correct
3. [ ] Check Railway service is running: `/health`
4. [ ] Review Chatwoot webhook logs for errors
5. [ ] Test endpoint manually with curl

**Solution:**
```bash
# Verify health
curl https://your-app.railway.app/health

# Check Railway logs
railway logs --tail

# Test webhook manually
curl -X POST https://your-app.railway.app/webhook/chatwoot \
  -H "Content-Type: application/json" \
  -H "X-Chatwoot-Signature: test" \
  -d '{"event":"message_created","message_type":"incoming","content":"test","conversation":{"id":123},"sender":{"phone_number":"+5594991398585"},"id":1,"created_at":1234567890}'
```

### Issue: 401 Unauthorized

**Symptoms:** Webhook returns 401 error

**Debug Steps:**
1. [ ] Check `CHATWOOT_WEBHOOK_SECRET` in Railway
2. [ ] Verify secret in Chatwoot matches exactly
3. [ ] Check for extra spaces or special characters
4. [ ] Review Railway logs for signature validation errors

**Solution:**
```bash
# Update secret in Railway
railway variables set CHATWOOT_WEBHOOK_SECRET="your-secret-here"

# Verify it's set
railway variables

# Redeploy
railway up
```

### Issue: Bot Not Responding

**Symptoms:** Webhook succeeds but no response in Chatwoot

**Debug Steps:**
1. [ ] Check Railway logs for agent processing errors
2. [ ] Verify LLM provider API key is valid
3. [ ] Check `CHATWOOT_API_TOKEN` is set correctly
4. [ ] Test Chatwoot API manually
5. [ ] Review agent orchestrator logs

**Solution:**
```bash
# Validate environment
python scripts/validate_env.py

# Check specific logs
railway logs --filter "agent_orchestrator"

# Test Chatwoot API
curl -X GET https://app.chatwoot.com/api/v1/accounts/{account_id}/conversations \
  -H "api_access_token: your-token"
```

### Issue: High Latency

**Symptoms:** Responses take > 7 seconds

**Debug Steps:**
1. [ ] Check LLM provider status page
2. [ ] Review P95 latency in dashboard
3. [ ] Check Redis connection
4. [ ] Review Supabase query performance
5. [ ] Check Railway resource usage

**Solution:**
```bash
# Check metrics
curl https://your-app.railway.app/metrics

# Consider switching LLM provider
railway variables set MODEL_PROVIDER="gemini"  # or "xai"

# Monitor improvement
railway logs --tail
```

### Issue: Logs Not Created

**Symptoms:** No logs in Supabase after processing

**Debug Steps:**
1. [ ] Check Supabase credentials in Railway
2. [ ] Verify `logs` table exists
3. [ ] Check Railway logs for Supabase errors
4. [ ] Test Supabase connection manually

**Solution:**
```bash
# Verify database
python scripts/verify_database.py

# Check Supabase credentials
railway variables | grep SUPABASE

# Test connection
python -c "from config.supabase_client import supabase; print(supabase.table('logs').select('*').limit(1).execute())"
```

---

## Performance Benchmarks

After completing all tests, verify these benchmarks:

### Response Time
- [ ] P95 latency ≤ 7 seconds
- [ ] Average latency ≤ 4 seconds
- [ ] No timeouts (> 30 seconds)

### Success Rate
- [ ] Webhook acceptance rate > 98%
- [ ] Message processing rate > 95%
- [ ] Response delivery rate > 95%

### Error Rate
- [ ] Overall error rate < 2%
- [ ] No 5xx errors in normal operation
- [ ] Graceful handling of all error types

### Conversation Quality
- [ ] FAQ responses are accurate
- [ ] Scheduling logic works correctly
- [ ] Escalation triggers appropriately
- [ ] Context maintained across messages

---

## Sign-Off

### Task 18.1 Sign-Off

- [ ] Webhook configured in Chatwoot
- [ ] Configuration tested and verified
- [ ] Documentation updated
- [ ] Team trained on configuration

**Completed by:** ________________  
**Date:** ________________  
**Notes:** ________________

### Task 18.2 Sign-Off

- [ ] All test scenarios passed
- [ ] End-to-end flow verified
- [ ] Performance benchmarks met
- [ ] Monitoring confirmed working

**Completed by:** ________________  
**Date:** ________________  
**Notes:** ________________

### Task 18 Complete

- [ ] Both subtasks completed
- [ ] All acceptance criteria met
- [ ] System ready for production use
- [ ] Handoff to operations team complete

**Final Sign-Off:** ________________  
**Date:** ________________

---

## Next Steps

After completing Task 18:

1. [ ] Move to Task 19: Execute QA manual testing
2. [ ] Monitor system for first 24 hours
3. [ ] Review metrics and adjust as needed
4. [ ] Document any issues or improvements
5. [ ] Train support team on troubleshooting

---

**Requirements:** 1.1, 1.5, 3.5
