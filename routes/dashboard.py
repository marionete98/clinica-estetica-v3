"""
Dashboard routes for observability UI.
Requirements: 8.3

Provides endpoints to serve the dashboard HTML and fetch dashboard data.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
from typing import Dict, Any
import os

from services.metrics import get_all_metrics


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ============================================================================
# DASHBOARD UI ENDPOINTS
# ============================================================================

@router.get("", response_class=HTMLResponse)
async def serve_dashboard():
    """
    Serve the dashboard HTML page.
    
    Returns:
        HTML page with observability dashboard
        
    Requirements: 8.3
    
    Example:
        GET /dashboard
        
        Returns: HTML page with metrics visualization
    """
    # Path to the static HTML file
    dashboard_path = os.path.join("static", "dashboard.html")
    
    # Check if file exists
    if not os.path.exists(dashboard_path):
        return HTMLResponse(
            content="""
            <html>
                <head><title>Dashboard Not Found</title></head>
                <body>
                    <h1>Dashboard não encontrado</h1>
                    <p>O arquivo static/dashboard.html não foi encontrado.</p>
                </body>
            </html>
            """,
            status_code=404
        )
    
    # Serve the HTML file
    return FileResponse(dashboard_path, media_type="text/html")


@router.get("/data", response_model=Dict[str, Any])
async def get_dashboard_data():
    """
    Get all dashboard data in JSON format.
    
    This endpoint is called by the dashboard frontend to fetch metrics data.
    It returns all metrics needed for the dashboard visualization.
    
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
        GET /dashboard/data
        
        Response:
        {
            "p95_latency_ms": 3450.0,
            "avg_latency_ms": 2100.5,
            "handover_rate_percent": 15.5,
            "conversion_rate_percent": 78.2,
            "cost_per_conversation_brl": 0.32,
            "total_cost_brl": 12.45,
            "error_rate_percent": 1.2,
            "recent_errors": [
                {
                    "ts": "2025-10-16T10:25:00Z",
                    "conversation_id": "cw_conv_123",
                    "intent": "schedule",
                    "error_message": "Timeout calling LLM",
                    "provider": "grok"
                }
            ],
            "timestamp": "2025-10-16T10:30:00Z"
        }
    """
    # Fetch all metrics from the metrics service
    metrics = await get_all_metrics()
    
    return metrics


# ============================================================================
# HEALTH CHECK FOR DASHBOARD
# ============================================================================

@router.get("/health", response_model=Dict[str, Any])
async def dashboard_health():
    """
    Health check endpoint for the dashboard service.
    
    Returns:
        Dictionary with health status
        
    Example:
        GET /dashboard/health
        
        Response:
        {
            "status": "healthy",
            "dashboard_available": true
        }
    """
    dashboard_path = os.path.join("static", "dashboard.html")
    dashboard_exists = os.path.exists(dashboard_path)
    
    return {
        "status": "healthy" if dashboard_exists else "degraded",
        "dashboard_available": dashboard_exists
    }
