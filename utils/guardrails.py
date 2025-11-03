"""
LLM guardrails module for Clínica Luana multi-agent scheduling system.
Implements safety limits and controls for LLM interactions.
"""

import time
from typing import Optional
import structlog

from config.redis_client import RedisClient
from services.container import get_redis_client
from config.settings import settings

logger = structlog.get_logger(__name__)


class GuardrailViolation(Exception):
    """Exception raised when a guardrail limit is exceeded."""

    def __init__(
        self, message: str, limit_type: str, current_value: int, max_value: int
    ):
        """
        Initialize guardrail violation exception.

        Args:
            message: Human-readable error message
            limit_type: Type of limit violated (e.g., 'tool_calls', 'tokens')
            current_value: Current value that exceeded the limit
            max_value: Maximum allowed value
        """
        self.message = message
        self.limit_type = limit_type
        self.current_value = current_value
        self.max_value = max_value
        super().__init__(self.message)


class LLMGuardrails:
    """
    Guardrails for LLM interactions to prevent abuse and control costs.

    Implements:
    - Tool call limits per session (max 3)
    - Token limits per response (max 500)
    - Token limits per conversation per hour (max 10,000)
    - User message prefixing for prompt injection protection
    """

    def __init__(self, redis_client: Optional[RedisClient] = None):
        """Initialize LLM guardrails."""
        self._redis = redis_client or get_redis_client()
        self.max_tool_calls_per_session = settings.max_tool_calls_per_session
        self.max_tokens_per_response = 500
        self.max_tokens_per_conversation_hour = 10000
        self.token_window_seconds = 3600  # 1 hour

    async def check_tool_call_limit(
        self, conversation_id: str, session_id: str
    ) -> bool:
        """
        Check if tool call limit has been exceeded for this session.

        Args:
            conversation_id: Conversation identifier
            session_id: Session identifier (unique per agent invocation)

        Returns:
            bool: True if within limit, False if exceeded

        Raises:
            GuardrailViolation: If limit is exceeded
        """
        try:
            key = f"guardrail:toolcalls:{conversation_id}:{session_id}"
            current_count = await self._redis.get_value(key, deserialize=False)

            if current_count is None:
                count = 0
            else:
                count = int(current_count)

            if count >= self.max_tool_calls_per_session:
                logger.warning(
                    "tool_call_limit_exceeded",
                    conversation_id=conversation_id,
                    session_id=session_id,
                    current_count=count,
                    max_allowed=self.max_tool_calls_per_session,
                )
                raise GuardrailViolation(
                    message=f"Tool call limit exceeded: {count}/{self.max_tool_calls_per_session}",
                    limit_type="tool_calls",
                    current_value=count,
                    max_value=self.max_tool_calls_per_session,
                )

            return True

        except GuardrailViolation:
            raise
        except Exception as e:
            logger.error(
                "tool_call_limit_check_failed",
                conversation_id=conversation_id,
                session_id=session_id,
                error=str(e),
            )
            # On error, allow the request (fail open)
            return True

    async def increment_tool_call_count(
        self, conversation_id: str, session_id: str
    ) -> int:
        """
        Increment tool call counter for this session.

        Args:
            conversation_id: Conversation identifier
            session_id: Session identifier

        Returns:
            int: New tool call count
        """
        try:
            key = f"guardrail:toolcalls:{conversation_id}:{session_id}"

            await self._redis.ensure_initialized()
            client = self._redis.client

            # Increment counter
            current = await client.incr(key)

            # Set expiry on first increment (1 hour)
            if current == 1:
                await client.expire(key, 3600)

            logger.debug(
                "tool_call_count_incremented",
                conversation_id=conversation_id,
                session_id=session_id,
                count=current,
                max_allowed=self.max_tool_calls_per_session,
            )

            return current

        except Exception as e:
            logger.error(
                "tool_call_increment_failed",
                conversation_id=conversation_id,
                session_id=session_id,
                error=str(e),
            )
            return 0

    def check_response_token_limit(self, estimated_tokens: int) -> bool:
        """
        Check if response token count is within limit.

        Args:
            estimated_tokens: Estimated number of tokens in response

        Returns:
            bool: True if within limit, False if exceeded

        Raises:
            GuardrailViolation: If limit is exceeded
        """
        if estimated_tokens > self.max_tokens_per_response:
            logger.warning(
                "response_token_limit_exceeded",
                estimated_tokens=estimated_tokens,
                max_allowed=self.max_tokens_per_response,
            )
            raise GuardrailViolation(
                message=f"Response token limit exceeded: {estimated_tokens}/{self.max_tokens_per_response}",
                limit_type="response_tokens",
                current_value=estimated_tokens,
                max_value=self.max_tokens_per_response,
            )

        return True

    async def check_conversation_token_limit(
        self, conversation_id: str, tokens_to_add: int
    ) -> bool:
        """
        Check if adding tokens would exceed hourly conversation limit.

        Args:
            conversation_id: Conversation identifier
            tokens_to_add: Number of tokens to add

        Returns:
            bool: True if within limit, False if exceeded

        Raises:
            GuardrailViolation: If limit is exceeded
        """
        try:
            current_hour = int(time.time() / self.token_window_seconds)
            key = f"guardrail:tokens:{conversation_id}:{current_hour}"

            current_tokens = await self._redis.get_value(key, deserialize=False)

            if current_tokens is None:
                total_tokens = tokens_to_add
            else:
                total_tokens = int(current_tokens) + tokens_to_add

            if total_tokens > self.max_tokens_per_conversation_hour:
                logger.warning(
                    "conversation_token_limit_exceeded",
                    conversation_id=conversation_id,
                    current_tokens=total_tokens,
                    max_allowed=self.max_tokens_per_conversation_hour,
                )
                raise GuardrailViolation(
                    message=f"Conversation token limit exceeded: {total_tokens}/{self.max_tokens_per_conversation_hour}",
                    limit_type="conversation_tokens",
                    current_value=total_tokens,
                    max_value=self.max_tokens_per_conversation_hour,
                )

            return True

        except GuardrailViolation:
            raise
        except Exception as e:
            logger.error(
                "conversation_token_limit_check_failed",
                conversation_id=conversation_id,
                error=str(e),
            )
            # On error, allow the request (fail open)
            return True

    async def increment_conversation_tokens(
        self, conversation_id: str, tokens: int
    ) -> int:
        """
        Increment token counter for this conversation hour.

        Args:
            conversation_id: Conversation identifier
            tokens: Number of tokens to add

        Returns:
            int: New total token count for this hour
        """
        try:
            current_hour = int(time.time() / self.token_window_seconds)
            key = f"guardrail:tokens:{conversation_id}:{current_hour}"

            await self._redis.ensure_initialized()
            client = self._redis.client

            # Increment counter
            current = await client.incrby(key, tokens)

            # Set expiry on first increment (1 hour)
            if current == tokens:
                await client.expire(key, self.token_window_seconds)

            logger.debug(
                "conversation_tokens_incremented",
                conversation_id=conversation_id,
                tokens_added=tokens,
                total_tokens=current,
                max_allowed=self.max_tokens_per_conversation_hour,
            )

            return current

        except Exception as e:
            logger.error(
                "conversation_token_increment_failed",
                conversation_id=conversation_id,
                error=str(e),
            )
            return 0

    def sanitize_user_message(self, message: str) -> str:
        """
        Sanitize user message to prevent prompt injection.
        Adds "User says:" prefix to clearly separate user input from system instructions.

        Args:
            message: Raw user message

        Returns:
            str: Sanitized message with prefix
        """
        # Strip any leading/trailing whitespace
        message = message.strip()

        # Add prefix to clearly mark user input
        sanitized = f"User says: {message}"

        logger.debug(
            "user_message_sanitized",
            original_length=len(message),
            sanitized_length=len(sanitized),
        )

        return sanitized

    async def get_tool_call_count(self, conversation_id: str, session_id: str) -> int:
        """
        Get current tool call count for session.

        Args:
            conversation_id: Conversation identifier
            session_id: Session identifier

        Returns:
            int: Current tool call count
        """
        try:
            key = f"guardrail:toolcalls:{conversation_id}:{session_id}"
            current_count = await self._redis.get_value(key, deserialize=False)

            if current_count is None:
                return 0

            return int(current_count)

        except Exception as e:
            logger.error(
                "tool_call_count_get_failed",
                conversation_id=conversation_id,
                session_id=session_id,
                error=str(e),
            )
            return 0

    async def get_conversation_token_count(self, conversation_id: str) -> int:
        """
        Get current token count for conversation in current hour.

        Args:
            conversation_id: Conversation identifier

        Returns:
            int: Current token count
        """
        try:
            current_hour = int(time.time() / self.token_window_seconds)
            key = f"guardrail:tokens:{conversation_id}:{current_hour}"

            current_tokens = await self._redis.get_value(key, deserialize=False)

            if current_tokens is None:
                return 0

            return int(current_tokens)

        except Exception as e:
            logger.error(
                "conversation_token_count_get_failed",
                conversation_id=conversation_id,
                error=str(e),
            )
            return 0

    async def reset_session_limits(self, conversation_id: str, session_id: str) -> None:
        """
        Reset all limits for a session (useful for testing or manual override).

        Args:
            conversation_id: Conversation identifier
            session_id: Session identifier
        """
        try:
            key = f"guardrail:toolcalls:{conversation_id}:{session_id}"

            await self._redis.ensure_initialized()
            await self._redis.client.delete(key)

            logger.info(
                "session_limits_reset",
                conversation_id=conversation_id,
                session_id=session_id,
            )

        except Exception as e:
            logger.error(
                "session_limits_reset_failed",
                conversation_id=conversation_id,
                session_id=session_id,
                error=str(e),
            )


# Global guardrails instance
guardrails = LLMGuardrails()


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    Uses simple heuristic: ~4 characters per token for English/Portuguese.

    Args:
        text: Text to estimate tokens for

    Returns:
        int: Estimated token count
    """
    # Simple estimation: 4 characters per token on average
    # This is a rough approximation for GPT-style tokenizers
    return max(1, len(text) // 4)


async def check_and_increment_tool_calls(
    conversation_id: str,
    session_id: str,
    guardrails_instance: Optional[LLMGuardrails] = None,
) -> int:
    """
    Helper function to check and increment tool call count in one operation.

    Args:
        conversation_id: Conversation identifier
        session_id: Session identifier
        guardrails_instance: Optional guardrails instance (uses global if None)

    Returns:
        int: New tool call count

    Raises:
        GuardrailViolation: If limit is exceeded
    """
    g = guardrails_instance or guardrails
    await g.check_tool_call_limit(conversation_id, session_id)
    return await g.increment_tool_call_count(conversation_id, session_id)


async def check_and_increment_tokens(
    conversation_id: str,
    tokens: int,
    guardrails_instance: Optional[LLMGuardrails] = None,
) -> int:
    """
    Helper function to check and increment token count in one operation.

    Args:
        conversation_id: Conversation identifier
        tokens: Number of tokens to add
        guardrails_instance: Optional guardrails instance (uses global if None)

    Returns:
        int: New total token count

    Raises:
        GuardrailViolation: If limit is exceeded
    """
    g = guardrails_instance or guardrails
    await g.check_conversation_token_limit(conversation_id, tokens)
    return await g.increment_conversation_tokens(conversation_id, tokens)

