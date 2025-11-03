# Observability System - Quick Start Guide

## Overview

The observability system provides real-time monitoring, metrics, and alerting for the Clínica Luana multi-agent scheduling system.

## Quick Access

### View Metrics Dashboard

```bash
# Get all metrics
curl http://localhost:8000/metrics

# Get summary (4 core metrics)
curl http://localhost:8000/metrics/summary

# Get specific metric
curl http://localhost:8000/metrics/latency?minutes=30
```

### Check Alerts

```bash
# View current alerts
curl http://localhost:8000/metrics/alerts

# Manually trigger alert check
curl -X POST http://localhost:8000/metrics/alerts/check
```

### View Recent Errors

```bash
# Get last 10 errors
curl http://localhost:8000/metrics/errors?limit=10
```

## Key Metrics

### 1. P95 Latency
**What it measures:** 95% of requests complete within this time  
**Target:** ≤ 7 seconds  
**Time window:** Last 10 minutes  
**Alert:** Critical if exceeded for 10 minutes

### 2. Handover Rate
**What it measures:** % of conversations escalated to humans  
**Target:** < 20%  
**Time window:** Last 1 hour  
**Alert:** Warning if > 30%

### 3. Booking Conversion Rate
**What it measures:** % of scheduling intents that result in bookings  
**Target:** > 70%  
**Time window:** Last 24 hours  
**Alert:** None (informational)

### 4. Cost per Conversation
**What it measures:** Average LLM cost per conversation  
**Target:** < R$ 0.50  
**Time window:** Last 24 hours  
**Alert:** None (informational)

## Using the Logger

### Basic Logging

```python
from utils.logger import logger

# Info log
logger.info(
    "Processing webhook",
    conversation_id="cw_conv_123",
    intent="schedule"
)

# Error log
logger.error(
    "Failed to create booking",
    conversation_id="cw_conv_123",
    error_message="Slot not available"
)
```

### Logging Agent Interactions

```python
from utils.logger import log_agent_interaction

await log_agent_interaction(
    conversation_id="cw_conv_123",
    contact_id=contact.id,
    intent="schedule",
    provider="xai",
    model="grok-4-reasoning",
    latency_ms=3450,
    tools_used=["list_available_slots", "create_booking"],
    input_tokens=1500,
    output_tokens=300,
    success=True
)
```

## Alert Configuration

Edit `.env` to configure alert thresholds:

```bash
# Latency threshold (milliseconds)
P95_LATENCY_THRESHOLD_MS=7000

# Error rate threshold (percentage)
ERROR_RATE_THRESHOLD_PERCENT=2.0

# Handover rate threshold (percentage)
HANDOVER_RATE_THRESHOLD_PERCENT=30.0

# Email alerts (optional)
ENABLE_EMAIL_ALERTS=false
ALERT_EMAIL=admin@example.com
```

## Monitoring in Production

### Railway Logs

All logs are automatically captured by Railway:
1. Go to Railway dashboard
2. Select your project
3. Click "Logs" tab
4. Filter by level or search for "ALERT"

### Scheduled Checks

The system automatically checks metrics every 5 minutes:
- P95 latency
- Error rate
- Handover rate

Alerts are logged to stdout and captured by Railway.

### Manual Monitoring

Set up a cron job to check metrics:

```bash
# Check every 5 minutes
*/5 * * * * curl -s http://your-app.railway.app/metrics/alerts | jq .
```

## Troubleshooting

### High Latency

**Symptoms:** P95 > 7 seconds

**Possible causes:**
- LLM provider slow/overloaded
- Database queries slow
- Network issues

**Actions:**
1. Check LLM provider status
2. Review slow queries in Supabase
3. Consider switching LLM provider
4. Scale up Railway instance

### High Error Rate

**Symptoms:** Error rate > 2%

**Possible causes:**
- LLM timeouts
- Database connection issues
- Invalid tool calls

**Actions:**
1. Check recent errors: `GET /metrics/errors`
2. Review error messages
3. Check external service status
4. Review agent prompts

### High Handover Rate

**Symptoms:** Handover rate > 30%

**Possible causes:**
- Agent prompts need improvement
- Knowledge base gaps
- Complex user requests
- Intent classification issues

**Actions:**
1. Review escalated conversations
2. Identify common patterns
3. Update knowledge base
4. Refine agent prompts
5. Add FAQ entries

## Best Practices

### 1. Regular Monitoring

- Check metrics dashboard daily
- Review weekly trends
- Investigate anomalies promptly

### 2. Cost Optimization

- Monitor cost per conversation
- Optimize prompt lengths
- Use Gemini for simple tasks
- Use Grok for complex reasoning

### 3. Performance Tuning

- Keep P95 latency < 5s for best UX
- Optimize database queries
- Use Redis caching effectively
- Minimize tool calls

### 4. Alert Response

- Respond to critical alerts within 15 minutes
- Document resolution steps
- Update runbooks
- Prevent recurrence

## API Reference

### GET /metrics

Returns all metrics including recent errors.

**Response:**
```json
{
  "p95_latency_ms": 3450.0,
  "avg_latency_ms": 2100.5,
  "handover_rate_percent": 15.5,
  "conversion_rate_percent": 78.2,
  "cost_per_conversation_brl": 0.32,
  "total_cost_brl": 12.45,
  "error_rate_percent": 1.2,
  "recent_errors": [...],
  "timestamp": "2025-10-16T10:30:00Z"
}
```

### GET /metrics/summary

Returns 4 core metrics for dashboard.

**Response:**
```json
{
  "p95_latency_ms": 3450.0,
  "handover_rate_percent": 15.5,
  "conversion_rate_percent": 78.2,
  "cost_per_conversation_brl": 0.32,
  "timestamp": "2025-10-16T10:30:00Z"
}
```

### GET /metrics/alerts

Returns current alert status.

**Response:**
```json
{
  "status": "healthy",
  "active_alerts": [],
  "alert_count": 0,
  "last_check": "2025-10-16T10:30:00Z"
}
```

### POST /metrics/alerts/check

Manually trigger alert check.

**Response:**
```json
{
  "alerts_triggered": 1,
  "alerts": [
    {
      "alert_type": "high_latency",
      "level": "critical",
      "message": "P95 latency exceeded threshold",
      "current_value": 8500.0,
      "threshold": 7000.0,
      "timestamp": "2025-10-16T10:30:00Z"
    }
  ]
}
```

## Support

For issues or questions:
1. Check Railway logs
2. Review recent errors in `/metrics/errors`
3. Check alert status in `/metrics/alerts`
4. Review this documentation
5. Contact system administrator

## Next Steps

1. Set up external monitoring (optional)
2. Create custom dashboard (task 14)
3. Configure email alerts
4. Set up metric retention policies
5. Implement trend analysis
