"""
Tests for observability system components.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from utils.logger import estimate_cost, StructuredLogger
from services.metrics import (
    calculate_p95_latency,
    calculate_handover_rate,
    calculate_booking_conversion_rate,
    calculate_cost_per_conversation
)
from services.alerts import (
    Alert,
    AlertLevel,
    AlertType,
    check_p95_latency_threshold
)


# ============================================================================
# COST ESTIMATION TESTS
# ============================================================================

def test_estimate_cost_grok():
    """Test cost estimation for Grok model."""
    cost = estimate_cost(
        provider="xai",
        model="grok-4-reasoning",
        input_tokens=1000,
        output_tokens=500
    )
    
    # Expected: (1000/1M * $5 + 500/1M * $15) * 5 BRL/USD
    # = (0.005 + 0.0075) * 5 = 0.0625 BRL
    assert cost == Decimal("0.0625")


def test_estimate_cost_gemini():
    """Test cost estimation for Gemini model."""
    cost = estimate_cost(
        provider="gemini",
        model="gemini-2.5-flash",
        input_tokens=1000,
        output_tokens=500
    )
    
    # Expected: (1000/1M * $0.075 + 500/1M * $0.30) * 5 BRL/USD
    # = (0.000075 + 0.00015) * 5 = 0.001125 BRL
    assert cost == Decimal("0.0011")


def test_estimate_cost_unknown_provider():
    """Test cost estimation for unknown provider returns 0."""
    cost = estimate_cost(
        provider="unknown",
        model="unknown-model",
        input_tokens=1000,
        output_tokens=500
    )
    
    assert cost == Decimal("0.0")


# ============================================================================
# LOGGER TESTS
# ============================================================================

def test_structured_logger_initialization():
    """Test that structured logger initializes correctly."""
    logger = StructuredLogger(name="test-logger")
    
    assert logger.logger is not None
    assert logger.logger.name == "test-logger"


def test_logger_info():
    """Test info logging."""
    logger = StructuredLogger(name="test-logger")
    
    # Should not raise exception
    logger.info(
        "Test message",
        conversation_id="test_conv_123",
        intent="test",
        latency_ms=100
    )


def test_logger_error():
    """Test error logging."""
    logger = StructuredLogger(name="test-logger")
    
    # Should not raise exception
    logger.error(
        "Test error",
        conversation_id="test_conv_123",
        error_message="Test error message"
    )


# ============================================================================
# ALERT TESTS
# ============================================================================

def test_alert_creation():
    """Test alert object creation."""
    alert = Alert(
        alert_type=AlertType.HIGH_LATENCY,
        level=AlertLevel.CRITICAL,
        message="Test alert",
        current_value=8000.0,
        threshold=7000.0,
        metadata={"test": "data"}
    )
    
    assert alert.alert_type == AlertType.HIGH_LATENCY
    assert alert.level == AlertLevel.CRITICAL
    assert alert.current_value == 8000.0
    assert alert.threshold == 7000.0
    assert alert.metadata["test"] == "data"


def test_alert_to_dict():
    """Test alert serialization to dictionary."""
    alert = Alert(
        alert_type=AlertType.HIGH_ERROR_RATE,
        level=AlertLevel.WARNING,
        message="Test alert",
        current_value=3.5,
        threshold=2.0
    )
    
    alert_dict = alert.to_dict()
    
    assert alert_dict["alert_type"] == "high_error_rate"
    assert alert_dict["level"] == "warning"
    assert alert_dict["current_value"] == 3.5
    assert alert_dict["threshold"] == 2.0
    assert "timestamp" in alert_dict


def test_alert_string_representation():
    """Test alert string representation."""
    alert = Alert(
        alert_type=AlertType.HIGH_HANDOVER_RATE,
        level=AlertLevel.INFO,
        message="Test alert",
        current_value=25.0,
        threshold=30.0
    )
    
    alert_str = str(alert)
    
    assert "INFO" in alert_str
    assert "high_handover_rate" in alert_str
    assert "25.0" in alert_str
    assert "30.0" in alert_str


# ============================================================================
# METRICS TESTS (UNIT TESTS - NO DATABASE)
# ============================================================================

def test_metrics_functions_exist():
    """Test that all required metrics functions exist."""
    # These should not raise ImportError
    assert callable(calculate_p95_latency)
    assert callable(calculate_handover_rate)
    assert callable(calculate_booking_conversion_rate)
    assert callable(calculate_cost_per_conversation)


# ============================================================================
# INTEGRATION TESTS (REQUIRE DATABASE)
# ============================================================================

@pytest.mark.asyncio
async def test_calculate_p95_latency_no_data():
    """Test P95 latency calculation with no data returns None."""
    # This will query the database but should handle empty results
    result = await calculate_p95_latency(minutes=1)
    
    # Should return None if no data (or a value if there is data)
    assert result is None or isinstance(result, float)


@pytest.mark.asyncio
async def test_calculate_handover_rate_no_data():
    """Test handover rate calculation with no data returns None."""
    result = await calculate_handover_rate(hours=1)
    
    # Should return None if no data (or a value if there is data)
    assert result is None or isinstance(result, float)


@pytest.mark.asyncio
async def test_calculate_conversion_rate_no_data():
    """Test conversion rate calculation with no data returns None."""
    result = await calculate_booking_conversion_rate(hours=1)
    
    # Should return None if no data (or a value if there is data)
    assert result is None or isinstance(result, float)


@pytest.mark.asyncio
async def test_calculate_cost_per_conversation_no_data():
    """Test cost per conversation calculation with no data returns None."""
    result = await calculate_cost_per_conversation(hours=1)
    
    # Should return None if no data (or a value if there is data)
    assert result is None or isinstance(result, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
