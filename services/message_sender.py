"""
Message Sender service for sending responses via Chatwoot API.
Handles retry logic, logging, and latency tracking.
Requirements: 1.5, 3.5, 8.2
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from config.chatwoot_client import chatwoot_client
from models.repositories.logs import create_log_entry
from utils.circuit_breakers import CircuitBreakerError, chatwoot_breaker

logger = logging.getLogger(__name__)


async def send_message(
    conversation_id: str, content: str, metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send a message via Chatwoot API with retry and logging.

    This function:
    1. Sends message via Chatwoot API
    2. Implements retry with exponential backoff
    3. Logs the send operation to Supabase
    4. Calculates and registers latency

    Args:
        conversation_id: Chatwoot conversation ID
        content: Message content to send
        metadata: Optional metadata about the message (intent, agent, etc.)

    Returns:
        Dictionary with send result:
        {
            "success": true,
            "message_id": "123",
            "latency_ms": 450,
            "error": null
        }

    Requirements: 1.5, 3.5, 8.2
    """
    start_time = datetime.now()

    try:
        logger.info(
            f"Sending message to conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "content_length": len(content),
            },
        )

        # Convert conversation_id to int for Chatwoot API
        try:
            conv_id_int = int(conversation_id)
        except ValueError:
            logger.error(f"Invalid conversation_id format: {conversation_id}")
            return {
                "success": False,
                "message_id": None,
                "latency_ms": 0,
                "error": "Invalid conversation_id format",
            }

        # Send message via Chatwoot (runs in thread pool to avoid blocking)
        def _call_chatwoot() -> Optional[dict[str, Any]]:
            return chatwoot_breaker.call(
                chatwoot_client.send_message,
                conv_id_int,
                content,
                "outgoing",
                False,
            )

        try:
            response = await asyncio.to_thread(_call_chatwoot)
        except CircuitBreakerError as cb_err:
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.warning(
                "Chatwoot circuit breaker open during send",
                extra={"conversation_id": conversation_id, "error": str(cb_err)},
            )
            await _log_message_send(
                conversation_id=conversation_id,
                message_id=None,
                latency_ms=latency_ms,
                metadata=metadata,
                success=False,
                error="chatwoot_breaker_open",
            )
            return {
                "success": False,
                "message_id": None,
                "latency_ms": latency_ms,
                "error": "Chatwoot temporarily unavailable; breaker open",
            }

        # Calculate latency
        latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        if response:
            message_id = response.get("id")

            logger.info(
                f"Message sent successfully: conversation={conversation_id}, "
                f"message_id={message_id}, latency={latency_ms}ms"
            )

            # Log to Supabase
            await _log_message_send(
                conversation_id=conversation_id,
                message_id=message_id,
                latency_ms=latency_ms,
                metadata=metadata,
                success=True,
            )

            return {
                "success": True,
                "message_id": message_id,
                "latency_ms": latency_ms,
                "error": None,
            }
        else:
            logger.error(
                f"Failed to send message to conversation {conversation_id} "
                f"after retries"
            )

            # Log failure to Supabase
            await _log_message_send(
                conversation_id=conversation_id,
                message_id=None,
                latency_ms=latency_ms,
                metadata=metadata,
                success=False,
                error="Failed after retries",
            )

            return {
                "success": False,
                "message_id": None,
                "latency_ms": latency_ms,
                "error": "Failed to send message after retries",
            }

    except Exception as e:
        latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        logger.error(
            f"Error sending message to conversation {conversation_id}: {e}",
            exc_info=True,
            extra={
                "conversation_id": conversation_id,
                "error": str(e),
            },
        )

        # Log error to Supabase
        await _log_message_send(
            conversation_id=conversation_id,
            message_id=None,
            latency_ms=latency_ms,
            metadata=metadata,
            success=False,
            error=str(e),
        )

        return {
            "success": False,
            "message_id": None,
            "latency_ms": latency_ms,
            "error": str(e),
        }


async def _log_message_send(
    conversation_id: str,
    message_id: Optional[int],
    latency_ms: int,
    metadata: Optional[Dict[str, Any]],
    success: bool,
    error: Optional[str] = None,
):
    """
    Log message send operation to Supabase.

    Args:
        conversation_id: Conversation identifier
        message_id: Chatwoot message ID (if successful)
        latency_ms: Latency in milliseconds
        metadata: Message metadata (intent, agent, provider, etc.)
        success: Whether send was successful
        error: Error message if failed
    """
    try:
        # Extract metadata fields
        intent = metadata.get("intent") if metadata else None
        agent = metadata.get("agent") if metadata else None
        provider = metadata.get("provider") if metadata else None
        contact_id = metadata.get("contact_id") if metadata else None
        tools_used = metadata.get("tools_used", []) if metadata else []
        cost_estimate = metadata.get("cost_estimate") if metadata else None

        # Create log entry
        await create_log_entry(
            conversation_id=conversation_id,
            contact_id=contact_id,
            intent=intent,
            provider=provider,
            latency_ms=latency_ms,
            tools_used=tools_used,
            cost_estimate=cost_estimate,
            error_message=error if not success else None,
            request_payload=None,  # Could add if needed
            response_payload={
                "message_id": message_id,
                "success": success,
                "agent": agent,
            }
            if success
            else None,
        )

        logger.debug(
            f"Logged message send: conversation={conversation_id}, "
            f"success={success}, latency={latency_ms}ms"
        )

    except Exception as e:
        # Don't fail the main operation if logging fails
        logger.error(
            f"Failed to log message send: {e}",
            exc_info=True,
            extra={
                "conversation_id": conversation_id,
                "error": str(e),
            },
        )


async def send_message_with_metadata(
    conversation_id: str,
    content: str,
    intent: Optional[str] = None,
    agent: Optional[str] = None,
    provider: Optional[str] = None,
    contact_id: Optional[str] = None,
    tools_used: Optional[list] = None,
    cost_estimate: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Convenience function to send message with explicit metadata fields.

    Args:
        conversation_id: Chatwoot conversation ID
        content: Message content
        intent: Classified intent
        agent: Agent that generated response
        provider: LLM provider used
        contact_id: Contact UUID
        tools_used: List of tools called
        cost_estimate: Estimated cost in currency

    Returns:
        Dictionary with send result
    """
    metadata = {
        "intent": intent,
        "agent": agent,
        "provider": provider,
        "contact_id": contact_id,
        "tools_used": tools_used or [],
        "cost_estimate": cost_estimate,
    }

    return await send_message(
        conversation_id=conversation_id, content=content, metadata=metadata
    )


async def send_notification(
    conversation_id: str, template_name: str, variables: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Send a notification message using a template.

    Useful for automated messages like confirmations, reminders, etc.

    Args:
        conversation_id: Chatwoot conversation ID
        template_name: Name of message template
        variables: Variables to fill in template

    Returns:
        Dictionary with send result
    """
    try:
        # Import here to avoid circular dependency
        from tools.kb_tools import format_template

        # Get formatted message from template
        formatted_message = await format_template(
            template_name=template_name, variables=variables or {}
        )

        if not formatted_message:
            logger.error(f"Failed to format template: {template_name}")
            return {
                "success": False,
                "message_id": None,
                "latency_ms": 0,
                "error": f"Template not found: {template_name}",
            }

        # Send the formatted message
        metadata = {
            "intent": "notification",
            "agent": "followup",
            "template_name": template_name,
        }

        return await send_message(
            conversation_id=conversation_id,
            content=formatted_message,
            metadata=metadata,
        )

    except Exception as e:
        logger.error(f"Error sending notification: {e}", exc_info=True)
        return {"success": False, "message_id": None, "latency_ms": 0, "error": str(e)}


async def send_escalation_message(conversation_id: str, summary: str) -> Dict[str, Any]:
    """
    Send escalation handoff message to the patient.

    Args:
        conversation_id: Chatwoot conversation ID
        summary: Conversation summary for context

    Returns:
        Dictionary with send result
    """
    message = (
        "Obrigado pela sua paciencia! :)\n\n"
        "Vou transferir voce para um de nossos especialistas que podera "
        "ajuda-lo melhor com sua solicitacao. Alguem da nossa equipe "
        "entrara em contato em breve.\n\n"
        "Aguarde um momento, por favor!"
    )

    metadata = {
        "intent": "escalation",
        "agent": "escalation",
        "summary": summary,
    }

    return await send_message(
        conversation_id=conversation_id,
        content=message,
        metadata=metadata,
    )

