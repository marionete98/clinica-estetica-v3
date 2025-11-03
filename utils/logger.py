"""
Structured logging module for observability.
Requirements: 8.1, 8.2

Provides JSON-formatted logging with automatic persistence to Supabase.
Includes cost estimation based on token usage.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from config.settings import settings
from services.container import get_supabase_ops


# ============================================================================
# COST ESTIMATION
# ============================================================================

# Token cost estimates (per 1M tokens) in USD
TOKEN_COSTS = {
    "xai": {
        "grok-4-reasoning": {
            "input": 5.00,  # $5 per 1M input tokens
            "output": 15.00  # $15 per 1M output tokens
        }
    },
    "gemini": {
        "gemini-2.5-flash": {
            "input": 0.075,  # $0.075 per 1M input tokens
            "output": 0.30   # $0.30 per 1M output tokens
        }
    }
}

# USD to BRL conversion rate (approximate)
USD_TO_BRL = 5.0


def estimate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int
) -> Decimal:
    """
    Estimate cost in BRL based on token usage.
    
    Args:
        provider: LLM provider ('xai' or 'gemini')
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Estimated cost in BRL
    """
    if provider not in TOKEN_COSTS:
        return Decimal("0.0")
    
    if model not in TOKEN_COSTS[provider]:
        return Decimal("0.0")
    
    costs = TOKEN_COSTS[provider][model]
    
    # Calculate cost in USD
    input_cost_usd = (input_tokens / 1_000_000) * costs["input"]
    output_cost_usd = (output_tokens / 1_000_000) * costs["output"]
    total_cost_usd = input_cost_usd + output_cost_usd
    
    # Convert to BRL
    total_cost_brl = Decimal(str(total_cost_usd * USD_TO_BRL))
    
    return total_cost_brl.quantize(Decimal("0.0001"))


# ============================================================================
# STRUCTURED LOGGER
# ============================================================================

class StructuredLogger:
    """
    Structured logger that outputs JSON and persists to Supabase.
    """
    
    def __init__(self, name: str = "clinica-luana"):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.log_level.upper()))
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add JSON handler for stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _log(
        self,
        level: str,
        message: str,
        conversation_id: Optional[str] = None,
        contact_id: Optional[UUID] = None,
        intent: Optional[str] = None,
        provider: Optional[str] = None,
        latency_ms: Optional[int] = None,
        tools_used: Optional[List[str]] = None,
        cost_estimate: Optional[Decimal] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Internal logging method with structured fields.
        
        Args:
            level: Log level (INFO, WARN, ERROR, DEBUG)
            message: Log message
            conversation_id: Chatwoot conversation ID
            contact_id: Contact UUID
            intent: Detected intent
            provider: LLM provider
            latency_ms: Response latency in milliseconds
            tools_used: List of tools called
            cost_estimate: Estimated cost in BRL
            error_message: Error message if any
            metadata: Additional metadata
        """
        extra = {
            "conversation_id": conversation_id,
            "contact_id": str(contact_id) if contact_id else None,
            "intent": intent,
            "provider": provider,
            "latency_ms": latency_ms,
            "tools_used": tools_used,
            "cost_estimate": float(cost_estimate) if cost_estimate else None,
            "error_message": error_message,
            "metadata": metadata or {}
        }
        
        log_method = getattr(self.logger, level.lower())
        log_method(message, extra=extra)
    
    def info(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        contact_id: Optional[UUID] = None,
        intent: Optional[str] = None,
        provider: Optional[str] = None,
        latency_ms: Optional[int] = None,
        tools_used: Optional[List[str]] = None,
        cost_estimate: Optional[Decimal] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log INFO level message."""
        self._log(
            "INFO", message, conversation_id, contact_id, intent,
            provider, latency_ms, tools_used, cost_estimate, None, metadata
        )
    
    def warning(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        contact_id: Optional[UUID] = None,
        intent: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log WARNING level message."""
        self._log(
            "WARNING", message, conversation_id, contact_id, intent,
            None, None, None, None, error_message, metadata
        )
    
    def error(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        contact_id: Optional[UUID] = None,
        intent: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log ERROR level message."""
        self._log(
            "ERROR", message, conversation_id, contact_id, intent,
            None, None, None, None, error_message, metadata
        )
    
    def debug(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log DEBUG level message."""
        self._log(
            "DEBUG", message, conversation_id, None, None,
            None, None, None, None, None, metadata
        )
    
    async def log_to_supabase(
        self,
        level: str = "INFO",
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        contact_id: Optional[UUID] = None,
        intent: Optional[str] = None,
        provider: Optional[str] = None,
        latency_ms: Optional[int] = None,
        tools_used: Optional[List[str]] = None,
        cost_estimate: Optional[Decimal] = None,
        error_message: Optional[str] = None,
        request_payload: Optional[Dict] = None,
        response_payload: Optional[Dict] = None
    ):
        """
        Persist log entry to Supabase logs table.
        
        Args:
            conversation_id: Chatwoot conversation ID
            contact_id: Contact UUID
            intent: Detected intent
            provider: LLM provider
            latency_ms: Response latency in milliseconds
            tools_used: List of tools called
            cost_estimate: Estimated cost in BRL
            error_message: Error message if any
            request_payload: Request data
            response_payload: Response data
        """
        try:
            enriched_request = dict(request_payload or {})
            enriched_request.setdefault("_log_level", level)
            if message is not None:
                enriched_request["_log_message"] = message
            if context:
                enriched_request["_log_context"] = context

            log_data = {
                "conversation_id": conversation_id,
                "contact_id": str(contact_id) if contact_id else None,
                "intent": intent,
                "provider": provider,
                "latency_ms": latency_ms,
                "tools_used": tools_used,
                "cost_estimate": float(cost_estimate) if cost_estimate else None,
                "error_message": error_message,
                "request_payload": enriched_request if enriched_request else None,
                "response_payload": response_payload
            }
            
            ops = get_supabase_ops()

            await asyncio.to_thread(
                ops.insert,
                "logs",
                log_data,
            )
            
        except Exception as e:
            # Don't fail the main operation if logging fails
            self.error(
                f"Failed to log to Supabase: {str(e)}",
                conversation_id=conversation_id,
                error_message=str(e)
            )


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "conversation_id") and record.conversation_id:
            log_data["conversation_id"] = record.conversation_id
        
        if hasattr(record, "contact_id") and record.contact_id:
            log_data["contact_id"] = record.contact_id
        
        if hasattr(record, "intent") and record.intent:
            log_data["intent"] = record.intent
        
        if hasattr(record, "provider") and record.provider:
            log_data["provider"] = record.provider
        
        if hasattr(record, "latency_ms") and record.latency_ms is not None:
            log_data["latency_ms"] = record.latency_ms
        
        if hasattr(record, "tools_used") and record.tools_used:
            log_data["tools_used"] = record.tools_used
        
        if hasattr(record, "cost_estimate") and record.cost_estimate is not None:
            log_data["cost_estimate"] = record.cost_estimate
        
        if hasattr(record, "error_message") and record.error_message:
            log_data["error_message"] = record.error_message
        
        if hasattr(record, "metadata") and record.metadata:
            log_data["metadata"] = record.metadata
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


# ============================================================================
# GLOBAL LOGGER INSTANCE
# ============================================================================

logger = StructuredLogger()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def log_agent_interaction(
    conversation_id: str,
    contact_id: Optional[UUID],
    intent: str,
    provider: str,
    model: str,
    latency_ms: int,
    tools_used: List[str],
    input_tokens: int,
    output_tokens: int,
    success: bool = True,
    error_message: Optional[str] = None
):
    """
    Log a complete agent interaction with automatic cost calculation.
    
    Args:
        conversation_id: Chatwoot conversation ID
        contact_id: Contact UUID
        intent: Detected intent
        provider: LLM provider
        model: Model name
        latency_ms: Response latency in milliseconds
        tools_used: List of tools called
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        success: Whether interaction was successful
        error_message: Error message if failed
    """
    # Calculate cost
    cost = estimate_cost(provider, model, input_tokens, output_tokens)
    
    # Log to stdout
    if success:
        logger.info(
            f"Agent interaction completed: {intent}",
            conversation_id=conversation_id,
            contact_id=contact_id,
            intent=intent,
            provider=provider,
            latency_ms=latency_ms,
            tools_used=tools_used,
            cost_estimate=cost,
            metadata={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        )
    else:
        logger.error(
            f"Agent interaction failed: {intent}",
            conversation_id=conversation_id,
            contact_id=contact_id,
            intent=intent,
            error_message=error_message,
            metadata={
                "model": model,
                "latency_ms": latency_ms
            }
        )
    
    # Persist to Supabase
    await logger.log_to_supabase(
        conversation_id=conversation_id,
        contact_id=contact_id,
        intent=intent,
        provider=provider,
        latency_ms=latency_ms,
        tools_used=tools_used,
        cost_estimate=cost,
        error_message=error_message
    )
