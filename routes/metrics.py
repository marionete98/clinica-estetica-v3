"""
Metrics API endpoints for observability.
Requirements: 8.3

Provides REST endpoints to query system metrics and recent errors.
"""

from fastapi import APIRouter, Query
from typing import Dict, Any

from services.metrics import (
    get_all_metrics,
    get_metrics_summary,
    calculate_p95_latency,
    calculate_handover_rate,
    calculate_booking_conversion_rate,
    calculate_cost_per_conversation,
    calculate_error_rate,
    get_recent_errors
)
from services.alerts import (
    get_alert_summary,
    run_alert_check
)
from tools.kb_tools_cached import get_cache_statistics


router = APIRouter(prefix="/metrics", tags=["metrics"])


# ============================================================================
# METRICS ENDPOINTS
# ============================================================================

@router.get("", response_model=Dict[str, Any])
async def get_metrics():
    """
    Get all key metrics in a single response.
    
    Returns:
        Dictionary containing:
        - p95_latency_ms: P95 latency (last 10 min)
        - avg_latency_ms: Average latency (last 10 min)
        - handover_rate_percent: Handover rate (last 1 hour)
        - conversion_rate_percent: Booking conversion (last 24 hours)
        - cost_per_conversation_brl: Cost per conversation (last 24 hours)
        - total_cost_brl: Total cost (last 24 hours)
        - error_rate_percent: Error rate (last 10 min)
        - recent_errors: Last 10 errors
        - timestamp: Current timestamp
        
    Requirements: 8.3
    
    Example:
        GET /metrics
        
        Response:
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
    """
    metrics = await get_all_metrics()
    return metrics


@router.get("/summary", response_model=Dict[str, Any])
async def get_summary():
    """
    Get summary of 4 core metrics for dashboard display.
    
    Returns:
        Dictionary containing:
        - p95_latency_ms: P95 latency (last 10 min)
        - handover_rate_percent: Handover rate (last 1 hour)
        - conversion_rate_percent: Booking conversion (last 24 hours)
        - cost_per_conversation_brl: Cost per conversation (last 24 hours)
        - timestamp: Current timestamp
        
    Requirements: 8.3
    
    Example:
        GET /metrics/summary
        
        Response:
        {
            "p95_latency_ms": 3450.0,
            "handover_rate_percent": 15.5,
            "conversion_rate_percent": 78.2,
            "cost_per_conversation_brl": 0.32,
            "timestamp": "2025-10-16T10:30:00Z"
        }
    """
    summary = await get_metrics_summary()
    return summary


@router.get("/latency", response_model=Dict[str, Any])
async def get_latency_metrics(
    minutes: int = Query(default=10, ge=1, le=1440, description="Time window in minutes")
):
    """
    Get latency metrics for a specific time window.
    
    Args:
        minutes: Time window in minutes (1-1440, default: 10)
        
    Returns:
        Dictionary with P95 latency
        
    Example:
        GET /metrics/latency?minutes=30
        
        Response:
        {
            "p95_latency_ms": 3200.0,
            "time_window_minutes": 30
        }
    """
    p95 = await calculate_p95_latency(minutes=minutes)
    
    return {
        "p95_latency_ms": p95,
        "time_window_minutes": minutes
    }


@router.get("/handover", response_model=Dict[str, Any])
async def get_handover_metrics(
    hours: int = Query(default=1, ge=1, le=168, description="Time window in hours")
):
    """
    Get handover rate for a specific time window.
    
    Args:
        hours: Time window in hours (1-168, default: 1)
        
    Returns:
        Dictionary with handover rate percentage
        
    Example:
        GET /metrics/handover?hours=24
        
        Response:
        {
            "handover_rate_percent": 18.5,
            "time_window_hours": 24
        }
    """
    rate = await calculate_handover_rate(hours=hours)
    
    return {
        "handover_rate_percent": rate,
        "time_window_hours": hours
    }


@router.get("/conversion", response_model=Dict[str, Any])
async def get_conversion_metrics(
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours")
):
    """
    Get booking conversion rate for a specific time window.
    
    Args:
        hours: Time window in hours (1-168, default: 24)
        
    Returns:
        Dictionary with conversion rate percentage
        
    Example:
        GET /metrics/conversion?hours=48
        
        Response:
        {
            "conversion_rate_percent": 75.3,
            "time_window_hours": 48
        }
    """
    rate = await calculate_booking_conversion_rate(hours=hours)
    
    return {
        "conversion_rate_percent": rate,
        "time_window_hours": hours
    }


@router.get("/cost", response_model=Dict[str, Any])
async def get_cost_metrics(
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours")
):
    """
    Get cost metrics for a specific time window.
    
    Args:
        hours: Time window in hours (1-168, default: 24)
        
    Returns:
        Dictionary with cost per conversation
        
    Example:
        GET /metrics/cost?hours=24
        
        Response:
        {
            "cost_per_conversation_brl": 0.32,
            "time_window_hours": 24
        }
    """
    cost = await calculate_cost_per_conversation(hours=hours)
    
    return {
        "cost_per_conversation_brl": cost,
        "time_window_hours": hours
    }


@router.get("/errors", response_model=Dict[str, Any])
async def get_error_metrics(
    minutes: int = Query(default=10, ge=1, le=1440, description="Time window in minutes"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of recent errors to return")
):
    """
    Get error rate and recent error logs.
    
    Args:
        minutes: Time window for error rate calculation (1-1440, default: 10)
        limit: Number of recent errors to return (1-100, default: 10)
        
    Returns:
        Dictionary with error rate and recent errors
        
    Requirements: 8.3
    
    Example:
        GET /metrics/errors?minutes=30&limit=5
        
        Response:
        {
            "error_rate_percent": 2.1,
            "time_window_minutes": 30,
            "recent_errors": [
                {
                    "ts": "2025-10-16T10:25:00Z",
                    "conversation_id": "cw_conv_123",
                    "intent": "schedule",
                    "error_message": "Timeout calling LLM",
                    "provider": "grok"
                },
                ...
            ]
        }
    """
    error_rate = await calculate_error_rate(minutes=minutes)
    recent_errors = await get_recent_errors(limit=limit)
    
    return {
        "error_rate_percent": error_rate,
        "time_window_minutes": minutes,
        "recent_errors": recent_errors
    }


# ============================================================================
# ALERTS ENDPOINTS
# ============================================================================

@router.get("/alerts", response_model=Dict[str, Any])
async def get_alerts():
    """
    Get current alert status and active alerts.
    
    Returns:
        Dictionary with alert status and list of active alerts
        
    Requirements: 8.4, 8.5
    
    Example:
        GET /metrics/alerts
        
        Response:
        {
            "status": "healthy",
            "active_alerts": [],
            "alert_count": 0,
            "last_check": "2025-10-16T10:30:00Z"
        }
    """
    summary = await get_alert_summary()
    return summary


@router.post("/alerts/check", response_model=Dict[str, Any])
async def trigger_alert_check():
    """
    Manually trigger an alert check cycle.
    
    Returns:
        List of active alerts found
        
    Requirements: 8.4, 8.5
    
    Example:
        POST /metrics/alerts/check
        
        Response:
        {
            "alerts_triggered": 1,
            "alerts": [
                {
                    "alert_type": "high_latency",
                    "level": "critical",
                    "message": "P95 latency exceeded threshold for 10 minutes",
                    "current_value": 8500.0,
                    "threshold": 7000.0,
                    "timestamp": "2025-10-16T10:30:00Z"
                }
            ]
        }
    """
    alerts = await run_alert_check()
    
    return {
        "alerts_triggered": len(alerts),
        "alerts": [alert.to_dict() for alert in alerts]
    }


# ============================================================================
# HEALTH CHECK WITH METRICS
# ============================================================================

@router.get("/health", response_model=Dict[str, Any])
async def metrics_health():
    """
    Health check endpoint that includes basic metrics status.
    
    Returns:
        Dictionary with health status and metric availability
        
    Example:
        GET /metrics/health
        
        Response:
        {
            "status": "healthy",
            "metrics_available": true,
            "p95_latency_ms": 3200.0
        }
    """
    try:
        # Try to get P95 latency as a health indicator
        p95 = await calculate_p95_latency(minutes=10)
        
        return {
            "status": "healthy",
            "metrics_available": p95 is not None,
            "p95_latency_ms": p95
        }
    except Exception as e:
        return {
            "status": "degraded",
            "metrics_available": False,
            "error": str(e)
        }


# ============================================================================
# KNOWLEDGE BASE CACHE METRICS
# ============================================================================

@router.get("/kb-cache", response_model=Dict[str, Any])
async def get_kb_cache_metrics():
    """
    Get knowledge base cache performance metrics.
    
    Returns:
        Dictionary with cache statistics and performance data
        
    Example:
        GET /metrics/kb-cache
        
        Response:
        {
            "total_entries": 45,
            "total_templates": 12,
            "last_sync": "2025-10-16T14:30:00Z",
            "cache_hits": 1250,
            "cache_misses": 45,
            "hit_rate": 0.965,
            "cache_size_mb": 2.3,
            "sync_interval_hours": 3,
            "cache_ttl_hours": 4,
            "status": "healthy"
        }
    """
    try:
        stats = await get_cache_statistics()
        return stats
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "total_entries": 0,
            "total_templates": 0,
            "hit_rate": 0.0
        }