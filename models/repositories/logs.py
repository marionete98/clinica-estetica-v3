"""
Structured logging repository operations.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from config.supabase_client import supabase_ops
from models.database import Log
from utils.circuit_breakers import CircuitBreakerError

logger = logging.getLogger(__name__)


async def create_log_entry(
    conversation_id: Optional[str] = None,
    contact_id: Optional[UUID] = None,
    intent: Optional[str] = None,
    provider: Optional[str] = None,
    latency_ms: Optional[int] = None,
    tools_used: Optional[List[str]] = None,
    cost_estimate: Optional[Decimal] = None,
    error_message: Optional[str] = None,
    request_payload: Optional[Dict] = None,
    response_payload: Optional[Dict] = None,
) -> Log:
    """
    Create a structured log entry for observability.
    """
    log_payload = {
        "conversation_id": conversation_id,
        "contact_id": str(contact_id) if contact_id else None,
        "intent": intent,
        "provider": provider,
        "latency_ms": latency_ms,
        "tools_used": tools_used,
        "cost_estimate": float(cost_estimate) if cost_estimate else None,
        "error_message": error_message,
        "request_payload": request_payload,
        "response_payload": response_payload,
    }

    try:
        rows = await supabase_ops.ainsert("logs", log_payload)
    except CircuitBreakerError as exc:
        logger.error(
            "supabase_log_insert_breaker_open",
            error=str(exc),
            conversation_id=conversation_id,
        )
        raise

    if not rows:
        raise RuntimeError("Supabase returned no data for log insert")

    return Log(**rows[0])


__all__ = ["create_log_entry"]
