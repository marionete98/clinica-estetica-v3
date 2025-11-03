# Railway Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Clínica Luana Multi-Agent System to Railway.

## Prerequisites

- Railway account (https://railway.app)
- GitHub repository connected to Railway
- Access to all required API keys and credentials

## Step 1: Configure Environment Variables

### Required Variables

Railway will automatically inject the `PORT` variable. You need to configure all other variables in the Railway dashboard.

### LLM Configuration

Choose your initial LLM provider (xai or gemini):

```bash
# Provider selection: 'xai' or 'gemini'
MODEL_PROVIDER=xai
```

#### For xAI Grok (Recommended for scheduling logic):

```bash
XAI_API_KEY=sk-your-xai-api-key-here
XAI_MODEL=grok-4-reasoning
XAI_BASE_URL=https://api.x.ai/v1
```

#### For Google Gemini (Recommended for FAQ):

```bash
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash
```

**Note:** Configure both providers even if you're only using one initially. This allows quick switching without redeployment.

### Database Configuration

```bash
# Supabase Postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-key-here
SUPABASE_JWT_SECRET=your-jwt-secret-here
```

**Important:** Use the `service_role` key, not the `anon` key, as the system needs full database access.

### Cache Configuration

```bash
# Redis Cloud
REDIS_URL=redis://default:password@your-redis-host:6379
REDIS_PASSWORD=your-redis-password
REDIS_HOST=your-redis-host.cloud.redislabs.com
REDIS_PORT=6379
```

**Note:** The `REDIS_URL` should include the password. The individual fields are for reference.

### Chatwoot Configuration

```bash
# Chatwoot API
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_ACCOUNT_ID=12345
CHATWOOT_API_TOKEN=your-chatwoot-api-token-here
CHATWOOT_WEBHOOK_SECRET=your-webhook-secret-here
```

**How to get these values:**
1. Log into Chatwoot
2. Go to Settings → Integrations → API
3. Create a new API access token
4. Note your account ID from the URL (e.g., `/app/accounts/12345/...`)
5. Generate a webhook secret (any random string, min 32 characters)

### Calendar API Integration

```bash
# External calendar system API
CALENDAR_API_URL=https://clinica-luana-calendar-production.up.railway.app/api
CALENDAR_API_TIMEOUT=10
```

### Application Configuration

```bash
# Environment
ENV=production

# Logging
LOG_LEVEL=INFO

# Agent Configuration
MAX_TOOL_CALLS_PER_SESSION=3
RESPONSE_TIMEOUT_SECONDS=10
MAX_CONTEXT_MESSAGES=20

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=100

# Business Hours (24h format)
BUSINESS_HOURS_START=08:30
BUSINESS_HOURS_END=19:00
BUSINESS_HOURS_SAT_END=12:00

# Policies
MIN_BOOKING_ADVANCE_HOURS=1
HARMONIZATION_CANCEL_HOURS=4
LASER_CANCEL_HOURS=24
MAX_RESCHEDULE_COUNT=2

# Reminders
REMINDER_D1_HOURS_BEFORE=24
REMINDER_H2_HOURS_BEFORE=2
```

### Monitoring and Observability

```bash
# Metrics thresholds
P95_LATENCY_THRESHOLD_MS=7000
ERROR_RATE_THRESHOLD_PERCENT=2
HANDOVER_RATE_THRESHOLD_PERCENT=30

# Alert configuration
ALERT_EMAIL=admin@clinicaluana.com.br
ENABLE_EMAIL_ALERTS=false
```

## Step 2: Validate API Keys

Before deploying, validate that all API keys are correct:

### Validate xAI API Key

```bash
curl -X POST https://api.x.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-4-reasoning",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }'
```

Expected: 200 OK response with completion

### Validate Gemini API Key

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"test"}]}]}'
```

Expected: 200 OK response with generated content

### Validate Supabase Connection

```bash
curl "YOUR_SUPABASE_URL/rest/v1/contacts?select=id&limit=1" \
  -H "apikey: YOUR_SUPABASE_KEY" \
  -H "Authorization: Bearer YOUR_SUPABASE_KEY"
```

Expected: 200 OK response (empty array is fine)

### Validate Redis Connection

Use a Redis client or the Railway Redis plugin dashboard to verify connectivity.

### Validate Chatwoot API

```bash
curl "YOUR_CHATWOOT_API_URL/api/v1/accounts/YOUR_ACCOUNT_ID/conversations" \
  -H "api_access_token: YOUR_CHATWOOT_API_TOKEN"
```

Expected: 200 OK response with conversations list

### Validate Calendar API

```bash
curl "https://clinica-luana-calendar-production.up.railway.app/api/health"
```

Expected: 200 OK response with health status

## Step 3: Railway Configuration Checklist

### Environment Variables Checklist

Use this checklist to ensure all variables are configured:

- [ ] `MODEL_PROVIDER` (xai or gemini)
- [ ] `XAI_API_KEY` (if using xAI)
- [ ] `XAI_MODEL` (default: grok-4-reasoning)
- [ ] `XAI_BASE_URL` (default: https://api.x.ai/v1)
- [ ] `GEMINI_API_KEY` (if using Gemini)
- [ ] `GEMINI_MODEL` (default: gemini-2.5-flash)
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_KEY` (service_role key)
- [ ] `SUPABASE_JWT_SECRET`
- [ ] `REDIS_URL`
- [ ] `REDIS_PASSWORD`
- [ ] `REDIS_HOST`
- [ ] `REDIS_PORT` (default: 6379)
- [ ] `CHATWOOT_API_URL`
- [ ] `CHATWOOT_ACCOUNT_ID`
- [ ] `CHATWOOT_API_TOKEN`
- [ ] `CHATWOOT_WEBHOOK_SECRET`
- [ ] `CALENDAR_API_URL`
- [ ] `CALENDAR_API_TIMEOUT` (default: 10)
- [ ] `ENV` (set to: production)
- [ ] `LOG_LEVEL` (default: INFO)
- [ ] All business configuration variables (optional, have defaults)

### Railway Service Configuration

1. **Service Name:** `clinica-luana-agent-system`
2. **Region:** Choose closest to your users (e.g., us-west1 for Brazil)
3. **Build Command:** Automatic (uses Dockerfile)
4. **Start Command:** Automatic (defined in Dockerfile)

### Health Check Configuration

Railway will use the Dockerfile's HEALTHCHECK directive:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"
```

**Manual Configuration (if needed):**
- **Path:** `/health`
- **Interval:** 30 seconds
- **Timeout:** 5 seconds
- **Retries:** 3

### Restart Policy

Configure in Railway dashboard:
- **On Failure:** Yes (automatic restart)
- **Max Restarts:** 5 per hour
- **Restart Delay:** 10 seconds

## Step 4: Security Best Practices

### Secrets Management

1. **Never commit secrets to Git**
   - All secrets should be in Railway environment variables
   - Use `.env.example` as a template only

2. **Rotate secrets regularly**
   - API keys: Every 90 days
   - Webhook secrets: Every 180 days
   - Database credentials: As needed

3. **Use strong webhook secrets**
   - Minimum 32 characters
   - Use a password generator
   - Example: `openssl rand -hex 32`

### Access Control

1. **Railway Project Access**
   - Limit team members with production access
   - Use separate staging environment for testing

2. **Supabase Access**
   - Use service_role key only in backend
   - Never expose service_role key to frontend
   - Enable RLS policies in Phase 2

3. **API Key Permissions**
   - Use minimum required permissions
   - Separate keys for dev/staging/production

## Step 5: Monitoring Setup

### Railway Logs

Railway automatically captures stdout/stderr. Configure log retention:
- **Retention:** 7 days (free tier) or 30 days (pro tier)
- **Log Level:** INFO in production, DEBUG in development

### Custom Metrics

The application exposes metrics at `/metrics`:
- P95 latency
- Handover rate
- Conversion rate
- Cost per conversation

### Alerts

Configure alerts in Railway:
1. **High CPU Usage:** > 80% for 5 minutes
2. **High Memory Usage:** > 90% for 5 minutes
3. **Deployment Failures:** Immediate notification
4. **Health Check Failures:** 3 consecutive failures

## Step 6: Deployment Verification

After deployment, verify the system is working:

### 1. Check Health Endpoint

```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "clinica-luana-agent-system",
  "version": "0.1.0",
  "timestamp": "2025-10-16T...",
  "checks": {
    "redis": true,
    "supabase": true,
    "chatwoot": true,
    "llm_config": true
  },
  "details": {
    "redis": "Connected",
    "supabase": "Connected",
    "chatwoot": "Connected",
    "llm_provider": "xAI (grok-4-reasoning)"
  }
}
```

### 2. Check Scheduler Status

```bash
curl https://your-app.railway.app/scheduler/status
```

Expected: 3 jobs running (reminder, feedback, alert_check)

### 3. Check Metrics Endpoint

```bash
curl https://your-app.railway.app/metrics
```

Expected: Metrics response (may be null initially)

### 4. Test Chat Endpoint

```bash
curl -X POST https://your-app.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+5594991398585",
    "message": "Olá, gostaria de agendar uma consulta"
  }'
```

Expected: Agent response with intent classification

### 5. Check Dashboard

Visit: `https://your-app.railway.app/dashboard`

Expected: Dashboard with metrics visualization

## Step 7: Post-Deployment Tasks

### 1. Configure Chatwoot Webhook

In Chatwoot dashboard:
1. Go to Settings → Integrations → Webhooks
2. Add new webhook:
   - **URL:** `https://your-app.railway.app/webhook/chatwoot`
   - **Events:** `message_created`
   - **Secret:** (use the CHATWOOT_WEBHOOK_SECRET value)

### 2. Test Webhook

Send a test message in Chatwoot and verify:
- Webhook is received (check Railway logs)
- Agent processes message
- Response is sent back to Chatwoot

### 3. Monitor Initial Traffic

For the first 24 hours:
- Check logs every 2 hours
- Monitor metrics dashboard
- Review error logs
- Verify scheduled jobs are running

## Troubleshooting

### Deployment Fails

**Symptom:** Build fails or container won't start

**Solutions:**
1. Check Railway build logs for errors
2. Verify Dockerfile syntax
3. Ensure all dependencies in requirements.txt
4. Check Python version compatibility (3.11+)

### Health Check Fails

**Symptom:** Service restarts repeatedly

**Solutions:**
1. Check `/health` endpoint manually
2. Verify all environment variables are set
3. Check database connectivity
4. Review application logs for startup errors

### High Latency

**Symptom:** P95 latency > 7 seconds

**Solutions:**
1. Check LLM provider status
2. Verify database query performance
3. Check Redis connectivity
4. Consider scaling to more instances

### Webhook Not Receiving Messages

**Symptom:** No messages processed from Chatwoot

**Solutions:**
1. Verify webhook URL is correct
2. Check webhook secret matches
3. Verify Chatwoot webhook is enabled
4. Check Railway logs for incoming requests
5. Test webhook with curl

## Scaling Considerations

### Vertical Scaling

Increase resources for single instance:
- **Memory:** Start with 512MB, scale to 1GB if needed
- **CPU:** Start with 0.5 vCPU, scale to 1 vCPU if needed

### Horizontal Scaling

Add more instances:
- **Trigger:** CPU > 70% for 5 minutes
- **Max Instances:** 3 (MVP), 10 (production)
- **Load Balancing:** Automatic via Railway

### Database Scaling

If Supabase becomes slow:
1. Add indexes to frequently queried columns
2. Optimize slow queries
3. Consider read replicas
4. Upgrade Supabase plan

## Cost Estimation

### Railway Costs

- **Starter Plan:** $5/month (512MB RAM, 0.5 vCPU)
- **Pro Plan:** $20/month (1GB RAM, 1 vCPU)
- **Scaling:** +$5-10 per additional instance

### Total Monthly Costs (1000 conversations)

- **Railway:** $5-15
- **LLM (xAI/Gemini):** $10-20
- **Supabase:** $0 (free tier)
- **Redis Cloud:** $0 (free tier)
- **Total:** $15-35/month

## Support and Maintenance

### Regular Maintenance Tasks

**Daily:**
- Check dashboard for anomalies
- Review error logs

**Weekly:**
- Review top 5 escalation reasons
- Update knowledge base if needed
- Check cost metrics

**Monthly:**
- Review and optimize prompts
- Update dependencies
- Rotate API keys (every 90 days)
- Review and optimize database queries

### Emergency Contacts

- **Railway Support:** https://railway.app/help
- **Supabase Support:** https://supabase.com/support
- **Chatwoot Support:** https://www.chatwoot.com/help-center

## Appendix: Quick Reference

### Railway CLI Commands

```bash
# Login to Railway
railway login

# Link to project
railway link

# View logs
railway logs

# View environment variables
railway variables

# Deploy manually
railway up
```

### Useful Endpoints

- **Health:** `GET /health`
- **Metrics:** `GET /metrics`
- **Dashboard:** `GET /dashboard`
- **Chat Test:** `POST /chat`
- **Scheduler Status:** `GET /scheduler/status`
- **Recent Errors:** `GET /metrics/recent-errors`

### Environment Variable Template

Copy this template to Railway's environment variables section:

```
MODEL_PROVIDER=xai
XAI_API_KEY=
XAI_MODEL=grok-4-reasoning
XAI_BASE_URL=https://api.x.ai/v1
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_JWT_SECRET=
REDIS_URL=
REDIS_PASSWORD=
REDIS_HOST=
REDIS_PORT=6379
CHATWOOT_API_URL=https://app.chatwoot.com
CHATWOOT_ACCOUNT_ID=
CHATWOOT_API_TOKEN=
CHATWOOT_WEBHOOK_SECRET=
CALENDAR_API_URL=https://clinica-luana-calendar-production.up.railway.app/api
CALENDAR_API_TIMEOUT=10
ENV=production
LOG_LEVEL=INFO
MAX_TOOL_CALLS_PER_SESSION=3
RESPONSE_TIMEOUT_SECONDS=10
MAX_CONTEXT_MESSAGES=20
MAX_REQUESTS_PER_MINUTE=100
BUSINESS_HOURS_START=08:30
BUSINESS_HOURS_END=19:00
BUSINESS_HOURS_SAT_END=12:00
MIN_BOOKING_ADVANCE_HOURS=1
HARMONIZATION_CANCEL_HOURS=4
LASER_CANCEL_HOURS=24
MAX_RESCHEDULE_COUNT=2
REMINDER_D1_HOURS_BEFORE=24
REMINDER_H2_HOURS_BEFORE=2
P95_LATENCY_THRESHOLD_MS=7000
ERROR_RATE_THRESHOLD_PERCENT=2
HANDOVER_RATE_THRESHOLD_PERCENT=30
ALERT_EMAIL=
ENABLE_EMAIL_ALERTS=false
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-16  
**Requirements:** 9.1, 9.2, 9.3, 9.4
