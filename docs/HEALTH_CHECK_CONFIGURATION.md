# Health Check Configuration

## Overview

The Clínica Luana Multi-Agent System implements comprehensive health checks to ensure system reliability and enable automatic recovery from failures.

## Health Check Endpoint

### Endpoint Details

- **Path:** `/health`
- **Method:** GET
- **Response Format:** JSON
- **Timeout:** 5 seconds
- **Authentication:** None (public endpoint)

### Response Schema

```json
{
  "status": "healthy" | "degraded",
  "service": "clinica-luana-agent-system",
  "version": "0.1.0",
  "timestamp": "2025-10-16T10:30:45.123Z",
  "checks": {
    "redis": true | false,
    "supabase": true | false,
    "chatwoot": true | false,
    "llm_config": true | false
  },
  "details": {
    "redis": "Connected" | "Error: ...",
    "supabase": "Connected" | "Error: ...",
    "chatwoot": "Connected" | "Error: ...",
    "llm_provider": "xAI (grok-4-reasoning)" | "Gemini (gemini-2.5-flash)"
  }
}
```

### Status Definitions

- **healthy:** All critical components are operational
- **degraded:** One or more components are failing, but system can still operate

### Component Checks

#### 1. Redis Check

**Purpose:** Verify cache/context storage is available

**Test:** 
- Set a test key with 10-second expiration
- Read the key back
- Verify value matches

**Failure Impact:** System operates in stateless mode (no conversation context)

**Critical:** No (graceful degradation)

#### 2. Supabase Check

**Purpose:** Verify database connectivity

**Test:**
- Execute simple SELECT query on contacts table
- Verify response is successful

**Failure Impact:** 
- FAQ agent can use cached knowledge base
- Scheduler agent cannot create bookings
- Logging is disabled

**Critical:** Yes (for scheduling operations)

#### 3. Chatwoot Check

**Purpose:** Verify messaging platform is reachable

**Test:**
- Call Chatwoot API health endpoint or list conversations
- Verify 200 OK response

**Failure Impact:**
- Cannot send messages to users
- Cannot receive webhooks
- System effectively offline

**Critical:** Yes

#### 4. LLM Configuration Check

**Purpose:** Verify LLM provider is properly configured

**Test:**
- Check MODEL_PROVIDER is set to 'xai' or 'gemini'
- Verify corresponding API key is present
- Verify model name is configured

**Failure Impact:**
- Agents cannot process messages
- System cannot respond to users

**Critical:** Yes

## Docker Health Check

### Configuration

The Dockerfile includes a built-in health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"
```

### Parameters

- **interval:** 30 seconds - Time between health checks
- **timeout:** 5 seconds - Maximum time to wait for response
- **start-period:** 10 seconds - Grace period during startup
- **retries:** 3 - Number of consecutive failures before marking unhealthy

### Behavior

1. **During Startup:**
   - Health checks begin after 10-second grace period
   - Allows time for application initialization
   - Failures during grace period don't count toward retry limit

2. **During Operation:**
   - Check runs every 30 seconds
   - If check fails, retry up to 3 times
   - After 3 consecutive failures, container marked unhealthy

3. **On Unhealthy:**
   - Railway automatically restarts the container
   - New container starts with fresh state
   - Health checks resume after grace period

## Railway Configuration

### Health Check Settings

Railway uses the Docker HEALTHCHECK directive automatically. Additional configuration in `railway.json`:

```json
{
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 5,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 5
  }
}
```

### Restart Policy

- **Type:** ON_FAILURE
- **Max Retries:** 5 per hour
- **Restart Delay:** 10 seconds (exponential backoff)

### Monitoring

Railway dashboard shows:
- Current health status (healthy/unhealthy)
- Last health check time
- Health check history (last 24 hours)
- Restart count

## Testing Health Checks

### Local Testing

```bash
# Start the application
uvicorn main:app --host 0.0.0.0 --port 8000

# Test health endpoint
curl http://localhost:8000/health

# Expected: 200 OK with JSON response
```

### Docker Testing

```bash
# Build image
docker build -t clinica-luana-agent .

# Run container
docker run -p 8000:8000 --env-file .env clinica-luana-agent

# Check health status
docker ps
# Look for "healthy" in STATUS column

# View health check logs
docker inspect --format='{{json .State.Health}}' <container_id> | jq
```

### Production Testing

```bash
# Test Railway deployment
curl https://your-app.railway.app/health

# Check all components
curl https://your-app.railway.app/health | jq '.checks'

# Monitor health over time
watch -n 5 'curl -s https://your-app.railway.app/health | jq ".status"'
```

## Troubleshooting

### Health Check Fails Immediately

**Symptom:** Container restarts continuously, never becomes healthy

**Possible Causes:**
1. Application fails to start
2. Port 8000 not accessible
3. Missing required environment variables
4. Database connection fails

**Solutions:**
1. Check Railway logs for startup errors
2. Verify all environment variables are set
3. Test database connectivity manually
4. Increase start-period if app needs more time to initialize

### Health Check Intermittent Failures

**Symptom:** Health check passes sometimes, fails other times

**Possible Causes:**
1. External service (Supabase, Redis, Chatwoot) is slow or unstable
2. Network latency issues
3. Resource constraints (CPU, memory)

**Solutions:**
1. Check external service status pages
2. Increase health check timeout
3. Scale up Railway instance resources
4. Implement retry logic in health check

### Health Check Always Degraded

**Symptom:** Status is "degraded" but container doesn't restart

**Possible Causes:**
1. Non-critical component (Redis) is down
2. LLM provider is slow but responding
3. Chatwoot API is rate-limited

**Solutions:**
1. Check component details in health response
2. Review logs for specific errors
3. Implement graceful degradation for non-critical components
4. Consider manual intervention for persistent issues

## Graceful Degradation

The system is designed to continue operating even when some components fail:

### Redis Unavailable

- **Impact:** No conversation context
- **Behavior:** Process each message independently
- **User Experience:** May need to repeat information
- **Recovery:** Automatic when Redis comes back online

### Supabase Slow

- **Impact:** Booking operations delayed
- **Behavior:** FAQ agent uses cached knowledge base
- **User Experience:** Slower responses, booking errors
- **Recovery:** Queue writes, retry when database recovers

### Chatwoot API Issues

- **Impact:** Cannot send/receive messages
- **Behavior:** Log errors, return 503 to webhooks
- **User Experience:** Messages not delivered
- **Recovery:** Chatwoot retries webhooks automatically

### LLM Provider Timeout

- **Impact:** Cannot generate responses
- **Behavior:** Return generic fallback message
- **User Experience:** Generic responses, escalation offered
- **Recovery:** Switch MODEL_PROVIDER or wait for recovery

## Monitoring and Alerts

### Health Check Metrics

Track these metrics in your monitoring system:

1. **Health Check Success Rate**
   - Target: > 99%
   - Alert: < 95% over 10 minutes

2. **Component Availability**
   - Track each component separately
   - Alert on any component < 95% over 10 minutes

3. **Restart Count**
   - Target: < 1 per day
   - Alert: > 3 per hour

4. **Health Check Latency**
   - Target: < 1 second
   - Alert: > 3 seconds average over 10 minutes

### Alert Configuration

Configure alerts in Railway:

1. **Critical Alert:** Health check fails 3 consecutive times
   - Action: Immediate notification
   - Escalation: Page on-call engineer

2. **Warning Alert:** Health check degraded for 10 minutes
   - Action: Email notification
   - Escalation: Review within 1 hour

3. **Info Alert:** Container restarted
   - Action: Log to monitoring system
   - Escalation: Review daily

## Best Practices

### 1. Keep Health Checks Fast

- Target: < 1 second response time
- Use connection pooling
- Cache results when appropriate
- Avoid expensive operations

### 2. Test Critical Paths Only

- Don't test every feature
- Focus on components that affect availability
- Balance thoroughness with speed

### 3. Implement Graceful Degradation

- System should handle component failures
- Provide degraded service rather than complete failure
- Document degradation behavior

### 4. Monitor Health Check Trends

- Track success rate over time
- Identify patterns in failures
- Proactively address degradation

### 5. Document Recovery Procedures

- Clear runbooks for each failure scenario
- Automated recovery where possible
- Manual intervention procedures documented

## Related Endpoints

### Scheduler Status

Check scheduled jobs health:

```bash
GET /scheduler/status
```

Returns status of APScheduler jobs (reminders, feedback, alerts).

### Metrics

Check system performance metrics:

```bash
GET /metrics
```

Returns P95 latency, handover rate, conversion rate, cost per conversation.

### Recent Errors

Check recent error logs:

```bash
GET /metrics/recent-errors?limit=10
```

Returns last 10 error log entries.

## References

- **Requirements:** 8.1 (Monitoring and observability)
- **Design Document:** Section "Observability and Monitoring"
- **Railway Documentation:** https://docs.railway.app/deploy/healthchecks
- **Docker Health Check:** https://docs.docker.com/engine/reference/builder/#healthcheck

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-16  
**Requirements:** 8.1
