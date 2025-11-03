"""
Webhook endpoints for receiving external events (Chatwoot).

This module provides two patterns for orchestrator lifecycle management:

1. **Dependency Injection Pattern (Current):**
   - Create orchestrator with `await create_orchestrator()`
   - Pass to background tasks
   - Cleanup in `finally` block
   - Good for FastAPI integration with explicit control

2. **Context Manager Pattern (Alternative):**
   - Use `async with orchestrator_lifespan()` for automatic cleanup
   - Cleaner code with guaranteed cleanup
   - Good for standalone scripts or simpler flows

Example of Context Manager Pattern:
    ```python
    from services.agent_orchestrator import orchestrator_lifespan

    async def process_message_with_context_manager(conv_id, phone, message):
        async with orchestrator_lifespan() as orchestrator:
            result = await orchestrator.orchestrate(conv_id, phone, message)
            # Process result...
        # Cleanup happens automatically here
    ```

Both patterns ensure proper resource cleanup and prevent memory leaks.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field, field_validator, ConfigDict

from config.settings import settings
from agents.agent_factory import AgentFactory, get_agent_factory
from config.redis_client import RedisClient
from config.supabase_client import SupabaseOperations
from services.container import get_redis_client, get_supabase_ops
from services.agent_orchestrator import AgentOrchestrator, create_orchestrator
from models.validation import ChatwootMessageInput
from utils.circuit_breakers import chatwoot_breaker, CircuitBreakerError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])

# Message deduplication cache
_processed_messages: Dict[str, datetime] = {}


# Message batching
@dataclass
class PendingMessage:
    content: str
    timestamp: int
    sender: Dict[str, Any]


_pending_messages: Dict[str, List[PendingMessage]] = {}
_processing_locks: Dict[str, asyncio.Lock] = {}
_TOKEN_VALIDATION_DISABLED_LOGGED = False


class ChatwootWebhookPayload(BaseModel):
    """Chatwoot webhook payload validation model."""

    event: str
    conversation: Dict[str, Any]
    message_type: str = Field(alias="message_type")
    content: str
    sender: Dict[str, Any]
    id: int
    created_at: int
    private: bool = False  # Filter private notes

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_created_at(cls, v):
        """Accept Unix timestamp (int) or ISO8601 string."""
        if isinstance(v, int):
            return v
        if isinstance(v, float):
            return int(v)
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("created_at cannot be empty")
            # Numeric string
            if v.isdigit():
                return int(v)
            try:
                # Support trailing Z to indicate UTC
                cleaned = v.replace("Z", "+00:00") if v.endswith("Z") else v
                dt = datetime.fromisoformat(cleaned)
                return int(dt.timestamp())
            except ValueError as exc:
                raise ValueError(
                    "created_at must be a Unix timestamp or ISO8601 string"
                ) from exc
        raise ValueError("created_at must be a Unix timestamp or ISO8601 string")

    @field_validator("content")
    @classmethod
    def content_length(cls, v):
        """Validate message content length."""
        if len(v) > 4000:
            raise ValueError("Message too long")
        return v

    @field_validator("message_type")
    @classmethod
    def only_incoming(cls, v):
        """Only process incoming messages."""
        if v != "incoming":
            raise ValueError("Only process incoming messages")
        return v

    @field_validator("private")
    @classmethod
    def no_private(cls, v):
        """Reject private messages (internal notes)."""
        if v:
            raise ValueError("Private messages not processed")
        return v


def is_duplicate_message(message_id: str) -> bool:
    """
    Check if message was already processed.

    Args:
        message_id: Chatwoot message ID

    Returns:
        True if duplicate, False otherwise
    """
    global _processed_messages
    now = datetime.now()
    cutoff = now - timedelta(seconds=settings.message_dedup_ttl_seconds)

    # Clean old entries
    _processed_messages = {
        mid: ts for mid, ts in _processed_messages.items() if ts > cutoff
    }

    # Check duplicate
    if message_id in _processed_messages:
        logger.warning(f"OU Duplicate message detected: {message_id}")
        return True

    # Mark as processed
    _processed_messages[message_id] = now
    return False


def validate_webhook_token(request: Request) -> bool:
    """
    Validate webhook authentication using token.

    Accepts token from:
    - Header: api_access_token (preferred)
    - Query param: ?token= (fallback)

    Args:
        request: FastAPI request object

    Returns:
        True if token is valid, False otherwise
    """
    import secrets

    global _TOKEN_VALIDATION_DISABLED_LOGGED
    expected_token = settings.chatwoot_webhook_token

    if not expected_token:
        if not _TOKEN_VALIDATION_DISABLED_LOGGED:
            logger.warning(
                "CHATWOOT_WEBHOOK_TOKEN not configured; skipping webhook token validation"
            )
            _TOKEN_VALIDATION_DISABLED_LOGGED = True
        return True

    # Accept token from header (preferred) or query param (fallback)
    header_token = request.headers.get("api_access_token")
    query_token = request.query_params.get("token")
    provided_token = header_token or query_token

    if not provided_token:
        logger.warning(
            f"Webhook received without api_access_token header or token query param from {request.client.host}"
        )
        return False

    # Validate token using constant-time comparison
    if not secrets.compare_digest(provided_token, expected_token):
        logger.warning(f"Invalid webhook token from {request.client.host}")
        return False

    logger.debug("Webhook token validated successfully")
    return True


async def collect_and_process_messages(
    conversation_id: str, initial_message: PendingMessage
) -> str:
    """
    Collect messages during delay period and return concatenated text.

    Args:
        conversation_id: Chatwoot conversation ID
        initial_message: First message that triggered processing

    Returns:
        Concatenated message content
    """
    delay = settings.message_processing_delay_seconds

    # Initialize list if not exists
    if conversation_id not in _pending_messages:
        _pending_messages[conversation_id] = []

    # Add initial message
    _pending_messages[conversation_id].append(initial_message)

    logger.info(f"⏳ Aguardando {delay}s por mensagens adicionais")

    # Wait for delay
    await asyncio.sleep(delay)

    # Collect all messages that arrived
    messages = _pending_messages[conversation_id].copy()
    _pending_messages[conversation_id] = []

    logger.info(f"📥 Coletadas {len(messages)} mensagens consecutivas")

    # Concatenate content
    concatenated = "\n".join(msg.content for msg in messages)

    return concatenated


async def process_chatwoot_message(
    conversation_id: str,
    phone: str,
    message: str,
    timestamp: int,
    sender: Dict[str, Any],
    orchestrator: AgentOrchestrator,
):
    """
    Process incoming Chatwoot message asynchronously.

    This function will be called as a background task to avoid blocking
    the webhook response. It now accepts an orchestrator instance to prevent
    race conditions between concurrent conversations.

    Args:
        conversation_id: Chatwoot conversation ID
        phone: Contact phone number
        message: Message content
        timestamp: Message timestamp
        sender: Sender information dict
        orchestrator: AgentOrchestrator instance for this request
    """
    try:
        logger.info(
            f"Processing message from conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "phone": phone,
                "timestamp": timestamp,
            },
        )

        # Import here to avoid circular dependencies
        from services.message_sender import send_message_with_metadata

        redis_client = get_redis_client()

        normalized_message = message.strip().lower()
        if normalized_message == "#reset#":
            reset_ok = False
            try:
                await redis_client.clear_context(conversation_id)
                await redis_client.delete_key(f"contact:{phone}")
                await redis_client.delete_key(f"session:{conversation_id}")
                reset_ok = True
                logger.info(
                    "Test conversation reset",
                    extra={"conversation_id": conversation_id, "phone": phone},
                )
            except Exception as reset_error:
                logger.error(
                    "Failed to reset conversation",
                    extra={
                        "conversation_id": conversation_id,
                        "error": str(reset_error),
                    },
                )
            if reset_ok:
                await send_message_with_metadata(
                    conversation_id=conversation_id,
                    content="Contexto de testes zerado. Pode continuar! O",
                    intent="system",
                    agent="system",
                    provider=None,
                    contact_id=None,
                    tools_used=None,
                    cost_estimate=None,
                )
            else:
                await send_message_with_metadata(
                    conversation_id=conversation_id,
                    content="Nuo consegui limpar o contexto agora. Tente novamente em instantes.",
                    intent="system",
                    agent="system",
                    provider=None,
                    contact_id=None,
                    tools_used=None,
                    cost_estimate=None,
                )
            return

        # Check if conversation is under human control
        try:
            state_key = f"session:{conversation_id}"
            state_data = await redis_client.get_value(state_key, deserialize=False)

            if state_data:
                import json

                state = json.loads(state_data)

                if state.get("automation_paused"):
                    logger.info(
                        f"👤 Conversa {conversation_id} sob controle humano - IA desabilitada"
                    )

                    # Notify agent via private note
                    from config.chatwoot_client import chatwoot_client

                    try:
                        await asyncio.to_thread(
                            chatwoot_breaker.call,
                            chatwoot_client.send_message,
                            int(conversation_id),
                            content=f"📨 **Nova mensagem do cliente:**\n\n{message}",
                            message_type="outgoing",
                            private=True,
                        )
                    except (ValueError, CircuitBreakerError) as notify_error:
                        logger.warning(
                            "Failed to send Chatwoot private note",
                            extra={"conversation_id": conversation_id, "error": str(notify_error)},
                        )
                    except Exception as notify_error:
                        logger.error(
                            f"Unexpected error sending Chatwoot note: {notify_error}",
                            exc_info=True,
                            extra={"conversation_id": conversation_id},
                        )
                    return
        except Exception as e:
            logger.warning(f"Could not check human takeover status: {e}")

        # Orchestrate agents to generate response using the provided orchestrator instance
        result = await orchestrator.orchestrate(conversation_id, phone, message)

        # Extract response and metadata
        response_text = result.get("response")
        intent = result.get("intent")
        agent = result.get("agent")
        should_escalate = result.get("should_escalate", False)
        metadata = result.get("metadata", {})

        # Send response if we have one (automation not paused)
        if response_text:
            await send_message_with_metadata(
                conversation_id=conversation_id,
                content=response_text,
                intent=intent,
                agent=agent,
                provider=metadata.get("provider"),
                contact_id=metadata.get("contact_id"),
                tools_used=metadata.get("tools_used"),
                cost_estimate=metadata.get("cost_estimate"),
            )

        # Handle escalation if needed
        if should_escalate:
            logger.info(f"Escalation needed for conversation {conversation_id}")
            # The escalation agent will handle assignment to human

        logger.info(
            f"Message processed successfully for conversation {conversation_id}"
        )

    except Exception as e:
        logger.error(
            f"Error processing message for conversation {conversation_id}: {str(e)}",
            exc_info=True,
            extra={
                "conversation_id": conversation_id,
                "error": str(e),
            },
        )
    finally:
        # Cleanup orchestrator resources after processing
        try:
            await orchestrator.cleanup()
            logger.debug(f"Orchestrator cleaned up for conversation {conversation_id}")
        except Exception as cleanup_error:
            logger.warning(
                f"Error during orchestrator cleanup for conversation {conversation_id}: {cleanup_error}"
            )


@router.post("/chatwoot")
async def chatwoot_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    agent_factory: AgentFactory = Depends(get_agent_factory),
    redis_client: RedisClient = Depends(get_redis_client),
    supabase_ops: SupabaseOperations = Depends(get_supabase_ops),
):
    """
    Receive and process Chatwoot webhook events.

    Authentication:
    - Header: api_access_token (preferred)
    - Query param: ?token= (fallback)

    This endpoint:
    1. Validates webhook token
    2. Filters events and message types
    3. Checks for duplicates
    4. Batches consecutive messages (7s delay)
    5. Checks human takeover status
    6. Processes asynchronously in background
    7. Returns 200 OK immediately

    Requirements: 1.1, 1.5
    """
    # Validate webhook token
    if not validate_webhook_token(request):
        logger.warning("Webhook authentication failed")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Parse JSON payload
    try:
        payload_dict = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Fast-path ignore for outgoing or private messages to avoid validation noise
    message_type = payload_dict.get("message_type")
    if message_type and message_type != "incoming":
        logger.debug(
            "Ignoring webhook with non-incoming message_type",
            extra={
                "message_type": message_type,
                "conversation": payload_dict.get("conversation", {}),
            },
        )
        return {"status": "ignored", "reason": "non_incoming_message"}

    if payload_dict.get("private"):
        logger.debug(
            "Ignoring private webhook message",
            extra={
                "conversation": payload_dict.get("conversation", {}),
                "message_id": payload_dict.get("id"),
            },
        )
        return {"status": "ignored", "reason": "private_message"}

    # Validate payload structure
    try:
        payload = ChatwootWebhookPayload(**payload_dict)
    except Exception as e:
        logger.warning(f"Invalid webhook payload structure: {str(e)}")
        # Return 200 to avoid Chatwoot retries for invalid payloads
        return {"status": "ignored", "reason": str(e)}

    # Extract required fields
    conversation_id = str(payload.conversation.get("id"))
    phone = payload.sender.get("phone_number", payload.sender.get("identifier", ""))
    message = payload.content
    timestamp = payload.created_at
    message_id = str(payload.id)

    # Validate we have required data
    if not conversation_id or not phone or not message:
        logger.warning(
            f"Missing required fields in webhook payload",
            extra={
                "conversation_id": conversation_id,
                "has_phone": bool(phone),
                "has_message": bool(message),
            },
        )
        return {"status": "ignored", "reason": "missing_fields"}

    # Validate and sanitize input using Pydantic model
    try:
        validated_input = ChatwootMessageInput(
            conversation_id=conversation_id,
            phone=phone,
            message=message,
            timestamp=timestamp,
            sender=payload.sender,
        )

        # Use validated and normalized values
        conversation_id = validated_input.conversation_id
        phone = validated_input.phone  # Now normalized to E.164 format
        message = validated_input.message  # Now sanitized

        logger.debug(
            "Input validated and sanitized",
            extra={
                "conversation_id": conversation_id,
                "phone": phone,
                "message_length": len(message),
            },
        )

    except Exception as e:
        logger.warning(
            f"Input validation failed for conversation {conversation_id}: {str(e)} - proceeding with raw phone/message",
            extra={"conversation_id": conversation_id, "phone": phone, "error": str(e)},
        )
        # Do not block processing on phone/message validation; continue with raw values

    # Check for duplicate message
    if is_duplicate_message(message_id):
        return {
            "status": "ignored",
            "reason": "duplicate_message",
            "message_id": message_id,
        }

    # Create lock for conversation if not exists
    if conversation_id not in _processing_locks:
        _processing_locks[conversation_id] = asyncio.Lock()

    # Check if already processing this conversation
    if _processing_locks[conversation_id].locked():
        # Add to pending messages queue
        pending_msg = PendingMessage(
            content=message, timestamp=timestamp, sender=payload.sender
        )
        if conversation_id not in _pending_messages:
            _pending_messages[conversation_id] = []
        _pending_messages[conversation_id].append(pending_msg)

        logger.info(f"oN Message added to batch for conversation {conversation_id}")

        return {
            "status": "queued",
            "conversation_id": conversation_id,
            "message": "Message added to batch",
        }

    # Create orchestrator instance for this request
    # Each request gets its own instance to prevent race conditions
    orchestrator = await create_orchestrator(
        agent_factory=agent_factory,
        redis_client=redis_client,
        supabase_ops=supabase_ops,
    )

    # Process with batching
    async def process_with_batching():
        async with _processing_locks[conversation_id]:
            pending_msg = PendingMessage(
                content=message, timestamp=timestamp, sender=payload.sender
            )

            # Collect messages with delay
            concatenated_message = await collect_and_process_messages(
                conversation_id, pending_msg
            )

            # Process concatenated message with the orchestrator instance
            await process_chatwoot_message(
                conversation_id=conversation_id,
                phone=phone,
                message=concatenated_message,
                timestamp=timestamp,
                sender=payload.sender,
                orchestrator=orchestrator,
            )

    # Start processing in background
    background_tasks.add_task(process_with_batching)

    # Return 200 OK immediately
    return {
        "status": "accepted",
        "conversation_id": conversation_id,
        "message": "Message queued for processing",
    }

