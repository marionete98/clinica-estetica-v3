"""
Metrics calculation service for observability.
Requirements: 8.1, 8.2, 8.3

Provides functions to calculate key performance metrics:
- P95 latency
- Handover rate
- Booking conversion rate
- Cost per conversation
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from decimal import Decimal

from services.container import get_supabase_client


# ============================================================================
# LATENCY METRICS
# ============================================================================

def _supabase():
    return get_supabase_client().client


async def calculate_p95_latency(minutes: int = 10) -> Optional[float]:
    """
    Calculate P95 latency for the last N minutes.
    
    P95 latency is the 95th percentile of response times, meaning 95% of
    requests were faster than this value.
    
    Args:
        minutes: Time window in minutes (default: 10)
        
    Returns:
        P95 latency in milliseconds, or None if no data
        
    Requirements: 8.1, 11.4
    """
    supabase = _supabase()
    
    # Calculate time threshold
    threshold = datetime.utcnow() - timedelta(minutes=minutes)
    
    # Query logs with latency data
    response = supabase.table("logs").select("latency_ms").gte(
        "ts", threshold.isoformat()
    ).not_.is_("latency_ms", "null").order("latency_ms").execute()
    
    if not response.data or len(response.data) == 0:
        return None
    
    latencies = [log["latency_ms"] for log in response.data]
    
    # Calculate P95 (95th percentile)
    p95_index = int(len(latencies) * 0.95)
    if p95_index >= len(latencies):
        p95_index = len(latencies) - 1
    
    return float(latencies[p95_index])


async def calculate_average_latency(minutes: int = 10) -> Optional[float]:
    """
    Calculate average latency for the last N minutes.
    
    Args:
        minutes: Time window in minutes (default: 10)
        
    Returns:
        Average latency in milliseconds, or None if no data
    """
    supabase = _supabase()
    
    threshold = datetime.utcnow() - timedelta(minutes=minutes)
    
    response = supabase.table("logs").select("latency_ms").gte(
        "ts", threshold.isoformat()
    ).not_.is_("latency_ms", "null").execute()
    
    if not response.data or len(response.data) == 0:
        return None
    
    latencies = [log["latency_ms"] for log in response.data]
    return sum(latencies) / len(latencies)


# ============================================================================
# HANDOVER METRICS
# ============================================================================

async def calculate_handover_rate(hours: int = 1) -> Optional[float]:
    """
    Calculate handover rate (escalation percentage) for the last N hours.
    
    Handover rate = (escalations / total conversations) * 100
    
    Args:
        hours: Time window in hours (default: 1)
        
    Returns:
        Handover rate as percentage (0-100), or None if no data
        
    Requirements: 8.2
    """
    supabase = _supabase()
    
    threshold = datetime.utcnow() - timedelta(hours=hours)
    
    # Count total conversations (unique conversation_ids with relevant intents)
    total_response = supabase.table("logs").select("conversation_id").gte(
        "ts", threshold.isoformat()
    ).in_(
        "intent", ["faq", "schedule", "reschedule", "cancel", "escalation"]
    ).execute()
    
    if not total_response.data or len(total_response.data) == 0:
        return None
    
    # Get unique conversation IDs
    unique_conversations = set(
        log["conversation_id"] 
        for log in total_response.data 
        if log["conversation_id"]
    )
    total_conversations = len(unique_conversations)
    
    if total_conversations == 0:
        return None
    
    # Count escalations
    escalation_response = supabase.table("logs").select("conversation_id").gte(
        "ts", threshold.isoformat()
    ).eq("intent", "escalation").execute()
    
    unique_escalations = set(
        log["conversation_id"] 
        for log in escalation_response.data 
        if log["conversation_id"]
    )
    escalation_count = len(unique_escalations)
    
    # Calculate percentage
    handover_rate = (escalation_count / total_conversations) * 100
    
    return round(handover_rate, 2)


# ============================================================================
# CONVERSION METRICS
# ============================================================================

async def calculate_booking_conversion_rate(hours: int = 24) -> Optional[float]:
    """
    Calculate booking conversion rate for the last N hours.
    
    Conversion rate = (successful bookings / scheduling intents) * 100
    
    Args:
        hours: Time window in hours (default: 24)
        
    Returns:
        Conversion rate as percentage (0-100), or None if no data
        
    Requirements: 8.2
    """
    supabase = _supabase()
    
    threshold = datetime.utcnow() - timedelta(hours=hours)
    
    # Count scheduling intents (unique conversations with schedule intent)
    schedule_response = supabase.table("logs").select("conversation_id").gte(
        "ts", threshold.isoformat()
    ).eq("intent", "schedule").execute()
    
    if not schedule_response.data or len(schedule_response.data) == 0:
        return None
    
    unique_schedule_conversations = set(
        log["conversation_id"] 
        for log in schedule_response.data 
        if log["conversation_id"]
    )
    schedule_count = len(unique_schedule_conversations)
    
    if schedule_count == 0:
        return None
    
    # Count successful bookings (appointments created in the same time window)
    appointments_response = supabase.table("appointments").select("conversation_id").gte(
        "created_at", threshold.isoformat()
    ).not_.is_("conversation_id", "null").execute()
    
    unique_booking_conversations = set(
        apt["conversation_id"] 
        for apt in appointments_response.data 
        if apt["conversation_id"]
    )
    booking_count = len(unique_booking_conversations)
    
    # Calculate percentage
    conversion_rate = (booking_count / schedule_count) * 100
    
    return round(conversion_rate, 2)


# ============================================================================
# COST METRICS
# ============================================================================

async def calculate_cost_per_conversation(hours: int = 24) -> Optional[float]:
    """
    Calculate average cost per conversation for the last N hours.
    
    Cost per conversation = total cost / unique conversations
    
    Args:
        hours: Time window in hours (default: 24)
        
    Returns:
        Average cost per conversation in BRL, or None if no data
        
    Requirements: 8.2
    """
    supabase = _supabase()
    
    threshold = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all logs with cost estimates
    response = supabase.table("logs").select("conversation_id, cost_estimate").gte(
        "ts", threshold.isoformat()
    ).not_.is_("cost_estimate", "null").execute()
    
    if not response.data or len(response.data) == 0:
        return None
    
    # Calculate total cost
    total_cost = sum(
        Decimal(str(log["cost_estimate"])) 
        for log in response.data 
        if log["cost_estimate"]
    )
    
    # Count unique conversations
    unique_conversations = set(
        log["conversation_id"] 
        for log in response.data 
        if log["conversation_id"]
    )
    conversation_count = len(unique_conversations)
    
    if conversation_count == 0:
        return None
    
    # Calculate average
    avg_cost = total_cost / conversation_count
    
    return round(float(avg_cost), 4)


async def calculate_total_cost(hours: int = 24) -> Optional[float]:
    """
    Calculate total cost for the last N hours.
    
    Args:
        hours: Time window in hours (default: 24)
        
    Returns:
        Total cost in BRL, or None if no data
    """
    supabase = _supabase()
    
    threshold = datetime.utcnow() - timedelta(hours=hours)
    
    response = supabase.table("logs").select("cost_estimate").gte(
        "ts", threshold.isoformat()
    ).not_.is_("cost_estimate", "null").execute()
    
    if not response.data or len(response.data) == 0:
        return None
    
    total_cost = sum(
        Decimal(str(log["cost_estimate"])) 
        for log in response.data 
        if log["cost_estimate"]
    )
    
    return round(float(total_cost), 4)


# ============================================================================
# ERROR METRICS
# ============================================================================

async def calculate_error_rate(minutes: int = 10) -> Optional[float]:
    """
    Calculate error rate for the last N minutes.
    
    Error rate = (errors / total logs) * 100
    
    Args:
        minutes: Time window in minutes (default: 10)
        
    Returns:
        Error rate as percentage (0-100), or None if no data
        
    Requirements: 8.4
    """
    supabase = _supabase()
    
    threshold = datetime.utcnow() - timedelta(minutes=minutes)
    
    # Count total logs
    total_response = supabase.table("logs").select("id", count="exact").gte(
        "ts", threshold.isoformat()
    ).execute()
    
    total_count = total_response.count if total_response.count else 0
    
    if total_count == 0:
        return None
    
    # Count errors (logs with error_message)
    error_response = supabase.table("logs").select("id", count="exact").gte(
        "ts", threshold.isoformat()
    ).not_.is_("error_message", "null").execute()
    
    error_count = error_response.count if error_response.count else 0
    
    # Calculate percentage
    error_rate = (error_count / total_count) * 100
    
    return round(error_rate, 2)


async def get_recent_errors(limit: int = 10) -> list:
    """
    Get the most recent error logs.
    
    Args:
        limit: Maximum number of errors to return (default: 10)
        
    Returns:
        List of error log entries
        
    Requirements: 8.3
    """
    supabase = _supabase()
    
    response = supabase.table("logs").select(
        "ts, conversation_id, intent, error_message, provider"
    ).not_.is_(
        "error_message", "null"
    ).order("ts", desc=True).limit(limit).execute()
    
    return response.data if response.data else []


# ============================================================================
# AGGREGATE METRICS
# ============================================================================

async def get_all_metrics() -> Dict[str, Any]:
    """
    Get all key metrics in a single call.
    
    Returns:
        Dictionary with all metrics:
        - p95_latency_ms: P95 latency (last 10 min)
        - avg_latency_ms: Average latency (last 10 min)
        - handover_rate_percent: Handover rate (last 1 hour)
        - conversion_rate_percent: Booking conversion (last 24 hours)
        - cost_per_conversation_brl: Cost per conversation (last 24 hours)
        - total_cost_brl: Total cost (last 24 hours)
        - error_rate_percent: Error rate (last 10 min)
        - recent_errors: Last 10 errors
        
    Requirements: 8.1, 8.2, 8.3
    """
    # Calculate all metrics concurrently would be ideal, but for simplicity
    # we'll calculate them sequentially
    
    p95_latency = await calculate_p95_latency(minutes=10)
    avg_latency = await calculate_average_latency(minutes=10)
    handover_rate = await calculate_handover_rate(hours=1)
    conversion_rate = await calculate_booking_conversion_rate(hours=24)
    cost_per_conv = await calculate_cost_per_conversation(hours=24)
    total_cost = await calculate_total_cost(hours=24)
    error_rate = await calculate_error_rate(minutes=10)
    recent_errors = await get_recent_errors(limit=10)
    
    return {
        "p95_latency_ms": p95_latency,
        "avg_latency_ms": avg_latency,
        "handover_rate_percent": handover_rate,
        "conversion_rate_percent": conversion_rate,
        "cost_per_conversation_brl": cost_per_conv,
        "total_cost_brl": total_cost,
        "error_rate_percent": error_rate,
        "recent_errors": recent_errors,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


async def get_metrics_summary() -> Dict[str, Any]:
    """
    Get a summary of the 4 core metrics for dashboard display.
    
    Returns:
        Dictionary with 4 core metrics:
        - p95_latency_ms: P95 latency (last 10 min)
        - handover_rate_percent: Handover rate (last 1 hour)
        - conversion_rate_percent: Booking conversion (last 24 hours)
        - cost_per_conversation_brl: Cost per conversation (last 24 hours)
        
    Requirements: 8.3
    """
    p95_latency = await calculate_p95_latency(minutes=10)
    handover_rate = await calculate_handover_rate(hours=1)
    conversion_rate = await calculate_booking_conversion_rate(hours=24)
    cost_per_conv = await calculate_cost_per_conversation(hours=24)
    
    return {
        "p95_latency_ms": p95_latency,
        "handover_rate_percent": handover_rate,
        "conversion_rate_percent": conversion_rate,
        "cost_per_conversation_brl": cost_per_conv,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
