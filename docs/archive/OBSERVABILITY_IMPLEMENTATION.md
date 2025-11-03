# Observability System Implementation

## Overview

This document describes the observability system implemented for the Clínica Luana multi-agent scheduling system.

**Implementation Date:** October 16, 2025  
**Requirements:** 8.1, 8.2, 8.3, 8.4, 8.5

## Components Implemented

### 1. Structured Logging Module (`utils/logger.py`)

**Features:**
- JSON-formatted logging for structured data
- Automatic persistence to Supabase `logs` table
- Cost estimation based on token usage
- Support for multiple log levels (INFO, WARNING, ERROR, DEBUG)

**Key Functions:**
- `logger.info()` - Log informational messages
- `logger.warning()` - Log warnings
- `logger.error()` - Log errors
- `logger.log_to_supabase()` - Persist logs to database
- `log_agent_interaction()` - Convenience function for logging complete agent interactions
- `estimate_cost()` - Calculate cost in BRL based on token usage

**Log Format:**
```json
{
  "timestamp": "2025-10-16T10:30:45.123Z",
  "level": "INFO",
  "message": "Agent interaction completed: schedule",
  "conversation_id": "cw_conv_12345",
  "contact_id": "uuid",
  "intent": "schedule",
  "provider": "grok",
  "latency_ms": 3450,
  "tools_used": ["list_available_slots", "create_booking"],
  "cost_estimate": 0.0234,
  "metadata": {
    "model": "grok-4-reasoning",
    "input_tokens": 1500,
    "output_tokens": 300
  }
}
```

**Cost Estimation:**
- xAI Grok-4-Reasoning: $5/1M input tokens, $15/1M output tokens
- Gemini 2.5 Flash: $0.075/1M input tokens, $0.30/1M output tokens
- Automatic conversion to BRL (USD × 5.0)

### 2. Metrics Calculation Service (`services/metrics.py`)

**Core Metrics:**

1. **P95 Latency** (`calculate_p95_latency`)
   - Time window: Last 10 minutes
   - Target: ≤ 7 seconds
   - Measures 95th percentile of response times

2. **Handover Rate** (`calculate_handover_rate`)
   - Time window: Last 1 hour
   - Target: < 20%
   - Formula: (escalations / total conversations) × 100

3. **Booking Conversion Rate** (`calculate_booking_conversion_rate`)
   - Time window: Last 24 hours
   - Target: > 70%
   - Formula: (successful bookings / scheduling intents) × 100

4. **Cost per Conversation** (`calculate_cost_per_conversation`)
   - Time window: Last 24 hours
   - Target: < R$ 0.50
   - Formula: total cost / unique conversations

**Additional Metrics:**
- Average latency
- Error rate
- Total cost
- Recent errors (last 10)

**Aggregate Functions:**
- `get_all_metrics()` - Returns all metrics in one call
- `get_metrics_summary()` - Returns 4 core metrics for dashboard

### 3. Metrics API Endpoints (`routes/metrics.py`)

**Endpoints:**

```
GET /metrics
- Returns all metrics including recent errors
- Response includes 8 key metrics + timestamp

GET /metrics/summary
- Returns 4 core metrics for dashboard display
- Optimized for quick overview

GET /metrics/latency?minutes=10
- Get P95 latency for custom time window
- Configurable time window (1-1440 minutes)

GET /metrics/handover?hours=1
- Get handover rate for custom time window
- Configurable time window (1-168 hours)

GET /metrics/conversion?hours=24
- Get booking conversion rate for custom time window
- Configurable time window (1-168 hours)

GET /metrics/cost?hours=24
- Get cost metrics for custom time window
- Configurable time window (1-168 hours)

GET /metrics/errors?minutes=10&limit=10
- Get error rate and recent error logs
- Configurable time window and error limit

GET /metrics/alerts
- Get current alert status and active alerts
- Returns alert summary with severity levels

POST /metrics/alerts/check
- Manually trigger alert check cycle
- Returns list of active alerts

GET /metrics/health
- Health check with basic metrics status
- Quick status indicator
```

### 4. Alert System (`services/alerts.py`)

**Alert Types:**
- `HIGH_LATENCY` - P95 latency exceeds threshold
- `HIGH_ERROR_RATE` - Error rate exceeds threshold
- `HIGH_HANDOVER_RATE` - Handover rate exceeds threshold
- `SERVICE_DEGRADED` - General service degradation

**Alert Levels:**
- `CRITICAL` - Immediate attention required
- `WARNING` - Should be reviewed soon
- `INFO` - Informational only

**Threshold Checks:**

1. **P95 Latency Check**
   - Threshold: 7000ms (configurable via `p95_latency_threshold_ms`)
   - Time window: 10 minutes
   - Level: CRITICAL

2. **Error Rate Check**
   - Threshold: 2.0% (configurable via `error_rate_threshold_percent`)
   - Time window: 10 minutes
   - Level: CRITICAL

3. **Handover Rate Check**
   - Threshold: 30.0% (configurable via `handover_rate_threshold_percent`)
   - Time window: 1 hour
   - Level: WARNING

**Alert Notifications:**
- Logs to stdout (Railway captures logs)
- Structured JSON format for parsing
- Email alerts (placeholder for future implementation)

**Scheduled Monitoring:**
- Alert check runs every 5 minutes via APScheduler
- Automatic threshold monitoring
- Alerts logged with full context

## Integration

### Main Application (`main.py`)

The observability system is integrated into the main FastAPI application:

1. **Metrics Router** - Registered at `/metrics` prefix
2. **Alert Check Job** - Scheduled every 5 minutes
3. **Startup Logging** - System initialization logged
4. **Shutdown Logging** - Graceful shutdown logged

### Configuration (`config/settings.py`)

Observability settings:
```python
p95_latency_threshold_ms: int = 7000
error_rate_threshold_percent: float = 2.0
handover_rate_threshold_percent: float = 30.0
alert_email: Optional[str] = None
enable_email_alerts: bool = False
```

## Usage Examples

### Importing Supabase Client

The logger module uses the global Supabase client instance:

```python
from config.supabase_client import supabase_client

# Access the client
supabase = supabase_client.client
```

**Note:** The old `get_supabase_client()` function pattern has been replaced with a global `supabase_client` instance for consistency and better connection management.

### Logging an Agent Interaction

```python
from utils.logger import log_agent_interaction

await log_agent_interaction(
    conversation_id="cw_conv_12345",
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

### Getting Metrics

```python
from services.metrics import get_metrics_summary

metrics = await get_metrics_summary()
# Returns: {
#   "p95_latency_ms": 3450.0,
#   "handover_rate_percent": 15.5,
#   "conversion_rate_percent": 78.2,
#   "cost_per_conversation_brl": 0.32,
#   "timestamp": "2025-10-16T10:30:00Z"
# }
```

### Checking Alerts

```python
from services.alerts import get_alert_summary

alert_status = await get_alert_summary()
# Returns: {
#   "status": "healthy",
#   "active_alerts": [],
#   "alert_count": 0,
#   "last_check": "2025-10-16T10:30:00Z"
# }
```

## Monitoring Dashboard

The metrics endpoints can be consumed by:
- Custom HTML dashboard (to be implemented in task 14)
- External monitoring tools (Grafana, Datadog, etc.)
- Railway logs and metrics
- Manual API calls for debugging

## Database Schema

The observability system uses the `logs` table in Supabase:

```sql
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ts TIMESTAMPTZ DEFAULT NOW(),
    conversation_id VARCHAR(255),
    contact_id UUID REFERENCES contacts(id),
    intent VARCHAR(50),
    provider VARCHAR(20),
    latency_ms INTEGER,
    tools_used TEXT[],
    cost_estimate DECIMAL(10,4),
    error_message TEXT,
    request_payload JSONB,
    response_payload JSONB
);

CREATE INDEX idx_logs_ts ON logs(ts DESC);
CREATE INDEX idx_logs_conversation ON logs(conversation_id);
CREATE INDEX idx_logs_intent ON logs(intent);
```

## Performance Considerations

1. **Metrics Calculation**
   - Queries are optimized with indexes
   - Time windows are configurable
   - Caching can be added for frequently accessed metrics

2. **Logging**
   - Asynchronous Supabase writes
   - Non-blocking stdout logging
   - Graceful degradation if logging fails

3. **Alerts**
   - Scheduled checks every 5 minutes
   - Minimal overhead on main request path
   - Configurable thresholds

## Future Enhancements

1. **Email Alerts** - Implement SMTP integration for critical alerts
2. **Dashboard UI** - Create HTML dashboard for real-time monitoring
3. **Metric Caching** - Add Redis caching for frequently accessed metrics
4. **Custom Alerts** - Allow configuration of custom alert rules
5. **Metric Aggregation** - Pre-calculate and store hourly/daily aggregates
6. **Trend Analysis** - Add trend detection and anomaly detection

## Testing

To test the observability system:

1. **Start the application:**
   ```bash
   uvicorn main:app --reload
   ```

2. **Access metrics:**
   ```bash
   curl http://localhost:8000/metrics/summary
   ```

3. **Check alerts:**
   ```bash
   curl http://localhost:8000/metrics/alerts
   ```

4. **Trigger manual alert check:**
   ```bash
   curl -X POST http://localhost:8000/metrics/alerts/check
   ```

## Compliance

This implementation satisfies the following requirements:
- **8.1** - Structured logging with latency tracking
- **8.2** - Metrics calculation (P95, handover rate, conversion, cost)
- **8.3** - Metrics API endpoints
- **8.4** - Alert system for P95 latency threshold
- **8.5** - Alert system for error rate threshold

## Conclusion

The observability system provides comprehensive monitoring and alerting capabilities for the Clínica Luana multi-agent scheduling system. It enables:
- Real-time performance monitoring
- Cost tracking and optimization
- Proactive issue detection
- Data-driven decision making
- Operational excellence

All components are production-ready and follow best practices for observability in distributed systems.
