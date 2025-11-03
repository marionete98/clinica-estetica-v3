"""
Alert system for monitoring critical metrics.
Requirements: 8.4, 8.5

Provides functions to check thresholds and trigger alerts when metrics
exceed acceptable limits.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from config.settings import settings
from services.metrics import (
    calculate_p95_latency,
    calculate_error_rate,
    calculate_handover_rate
)


logger = logging.getLogger(__name__)


# ============================================================================
# ALERT TYPES
# ============================================================================

class AlertLevel(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertType(str, Enum):
    """Types of alerts."""
    HIGH_LATENCY = "high_latency"
    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_HANDOVER_RATE = "high_handover_rate"
    SERVICE_DEGRADED = "service_degraded"


# ============================================================================
# ALERT DATA STRUCTURE
# ============================================================================

class Alert:
    """Alert data structure."""
    
    def __init__(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        message: str,
        current_value: float,
        threshold: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.alert_type = alert_type
        self.level = level
        self.message = message
        self.current_value = current_value
        self.threshold = threshold
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_type": self.alert_type.value,
            "level": self.level.value,
            "message": self.message,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    def __str__(self) -> str:
        """String representation for logging."""
        return (
            f"[{self.level.value.upper()}] {self.alert_type.value}: "
            f"{self.message} (current: {self.current_value}, threshold: {self.threshold})"
        )


# ============================================================================
# THRESHOLD CHECKS
# ============================================================================

async def check_p95_latency_threshold(minutes: int = 10) -> Optional[Alert]:
    """
    Check if P95 latency exceeds threshold.
    
    Args:
        minutes: Time window in minutes (default: 10)
        
    Returns:
        Alert object if threshold exceeded, None otherwise
        
    Requirements: 8.4
    """
    try:
        p95_latency = await calculate_p95_latency(minutes=minutes)
        
        if p95_latency is None:
            return None
        
        threshold = settings.p95_latency_threshold_ms
        
        if p95_latency > threshold:
            return Alert(
                alert_type=AlertType.HIGH_LATENCY,
                level=AlertLevel.CRITICAL,
                message=f"P95 latency exceeded threshold for {minutes} minutes",
                current_value=p95_latency,
                threshold=threshold,
                metadata={
                    "time_window_minutes": minutes,
                    "unit": "milliseconds"
                }
            )
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking P95 latency threshold: {e}")
        return None


async def check_error_rate_threshold(minutes: int = 10) -> Optional[Alert]:
    """
    Check if error rate exceeds threshold.
    
    Args:
        minutes: Time window in minutes (default: 10)
        
    Returns:
        Alert object if threshold exceeded, None otherwise
        
    Requirements: 8.5
    """
    try:
        error_rate = await calculate_error_rate(minutes=minutes)
        
        if error_rate is None:
            return None
        
        threshold = settings.error_rate_threshold_percent
        
        if error_rate > threshold:
            return Alert(
                alert_type=AlertType.HIGH_ERROR_RATE,
                level=AlertLevel.CRITICAL,
                message=f"Error rate exceeded threshold for {minutes} minutes",
                current_value=error_rate,
                threshold=threshold,
                metadata={
                    "time_window_minutes": minutes,
                    "unit": "percent"
                }
            )
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking error rate threshold: {e}")
        return None


async def check_handover_rate_threshold(hours: int = 1) -> Optional[Alert]:
    """
    Check if handover rate exceeds threshold.
    
    Args:
        hours: Time window in hours (default: 1)
        
    Returns:
        Alert object if threshold exceeded, None otherwise
        
    Requirements: 8.4
    """
    try:
        handover_rate = await calculate_handover_rate(hours=hours)
        
        if handover_rate is None:
            return None
        
        threshold = settings.handover_rate_threshold_percent
        
        if handover_rate > threshold:
            return Alert(
                alert_type=AlertType.HIGH_HANDOVER_RATE,
                level=AlertLevel.WARNING,
                message=f"Handover rate exceeded threshold for {hours} hour(s)",
                current_value=handover_rate,
                threshold=threshold,
                metadata={
                    "time_window_hours": hours,
                    "unit": "percent"
                }
            )
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking handover rate threshold: {e}")
        return None


# ============================================================================
# ALERT CHECKING
# ============================================================================

async def check_all_thresholds() -> List[Alert]:
    """
    Check all metric thresholds and return active alerts.
    
    Returns:
        List of Alert objects for metrics exceeding thresholds
        
    Requirements: 8.4, 8.5
    """
    alerts = []
    
    # Check P95 latency (last 10 minutes)
    latency_alert = await check_p95_latency_threshold(minutes=10)
    if latency_alert:
        alerts.append(latency_alert)
    
    # Check error rate (last 10 minutes)
    error_alert = await check_error_rate_threshold(minutes=10)
    if error_alert:
        alerts.append(error_alert)
    
    # Check handover rate (last 1 hour)
    handover_alert = await check_handover_rate_threshold(hours=1)
    if handover_alert:
        alerts.append(handover_alert)
    
    return alerts


# ============================================================================
# ALERT NOTIFICATION
# ============================================================================

def log_alert(alert: Alert):
    """
    Log alert to stdout (Railway captures logs).
    
    Args:
        alert: Alert object to log
        
    Requirements: 8.4, 8.5
    """
    if alert.level == AlertLevel.CRITICAL:
        logger.critical(str(alert))
    elif alert.level == AlertLevel.WARNING:
        logger.warning(str(alert))
    else:
        logger.info(str(alert))
    
    # Log structured data for parsing
    logger.info(
        "ALERT_DATA",
        extra={
            "alert_type": alert.alert_type.value,
            "level": alert.level.value,
            "current_value": alert.current_value,
            "threshold": alert.threshold,
            "timestamp": alert.timestamp
        }
    )


async def send_email_alert(alert: Alert):
    """
    Send email alert (placeholder for future implementation).
    
    Args:
        alert: Alert object to send
        
    Note:
        This is a placeholder. Email sending would require:
        - SMTP configuration
        - Email template
        - Recipient list
        
    Requirements: 8.4, 8.5
    """
    if not settings.enable_email_alerts or not settings.alert_email:
        return
    
    # TODO: Implement email sending
    # For now, just log that we would send an email
    logger.info(
        f"Email alert would be sent to {settings.alert_email}: {alert.message}"
    )


async def trigger_alerts(alerts: List[Alert]):
    """
    Trigger notifications for all alerts.
    
    Args:
        alerts: List of Alert objects to trigger
        
    Requirements: 8.4, 8.5
    """
    for alert in alerts:
        # Always log to stdout (Railway captures)
        log_alert(alert)
        
        # Send email if enabled and alert is critical
        if alert.level == AlertLevel.CRITICAL:
            await send_email_alert(alert)


# ============================================================================
# MONITORING LOOP
# ============================================================================

async def run_alert_check():
    """
    Run a single alert check cycle.
    
    This function should be called periodically (e.g., every 5 minutes)
    to monitor metrics and trigger alerts.
    
    Returns:
        List of active alerts
        
    Requirements: 8.4, 8.5
    """
    try:
        logger.debug("Running alert check cycle")
        
        # Check all thresholds
        alerts = await check_all_thresholds()
        
        if alerts:
            logger.info(f"Found {len(alerts)} active alert(s)")
            await trigger_alerts(alerts)
        else:
            logger.debug("No alerts triggered")
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error in alert check cycle: {e}", exc_info=True)
        return []


# ============================================================================
# ALERT SUMMARY
# ============================================================================

async def get_alert_summary() -> Dict[str, Any]:
    """
    Get summary of current alert status.
    
    Returns:
        Dictionary with alert status and active alerts
        
    Example:
        {
            "status": "healthy",
            "active_alerts": [],
            "last_check": "2025-10-16T10:30:00Z"
        }
    """
    alerts = await check_all_thresholds()
    
    # Determine overall status
    if any(alert.level == AlertLevel.CRITICAL for alert in alerts):
        status = "critical"
    elif any(alert.level == AlertLevel.WARNING for alert in alerts):
        status = "warning"
    else:
        status = "healthy"
    
    return {
        "status": status,
        "active_alerts": [alert.to_dict() for alert in alerts],
        "alert_count": len(alerts),
        "last_check": datetime.utcnow().isoformat() + "Z"
    }
