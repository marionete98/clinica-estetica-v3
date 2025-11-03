"""
Rate limiting middleware for webhook endpoints.
Uses Redis to track request counts per conversation_id.
"""

import time
from typing import Callable, Optional
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from config.redis_client import RedisClient
from config.settings import settings
from services.container import get_redis_client

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware that limits requests per conversation_id.

    Limits webhook endpoint to MAX_REQUESTS_PER_MINUTE requests per minute
    per conversation_id using Redis counters.
    """

    def __init__(
        self,
        app,
        paths_to_limit: Optional[list[str]] = None,
        redis_client: Optional[RedisClient] = None,
    ):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI application instance
            paths_to_limit: List of path prefixes to apply rate limiting to
                           (default: ["/webhooks/"])
        """
        super().__init__(app)
        self.paths_to_limit = paths_to_limit or ["/webhooks/"]
        self.max_requests = settings.max_requests_per_minute
        self.window_seconds = 60  # 1 minute window
        self.redis_client = redis_client or get_redis_client()

    def _should_rate_limit(self, path: str) -> bool:
        """
        Check if the request path should be rate limited.

        Args:
            path: Request path

        Returns:
            bool: True if path should be rate limited
        """
        return any(path.startswith(prefix) for prefix in self.paths_to_limit)

    def _get_rate_limit_key(self, conversation_id: str) -> str:
        """
        Get Redis key for rate limiting counter.

        Args:
            conversation_id: Conversation identifier

        Returns:
            str: Redis key for rate limit counter
        """
        current_minute = int(time.time() / self.window_seconds)
        return f"ratelimit:{conversation_id}:{current_minute}"

    def _extract_conversation_id(self, request: Request) -> str | None:
        """
        Extract conversation_id from request.

        Tries to extract from:
        1. Query parameters
        2. Request body (if JSON)
        3. Path parameters

        Args:
            request: FastAPI request object

        Returns:
            str | None: Conversation ID if found, None otherwise
        """
        # Try query parameters
        conversation_id = request.query_params.get("conversation_id")
        if conversation_id:
            return str(conversation_id)

        # Try to get from request state (set by webhook handler)
        if hasattr(request.state, "conversation_id"):
            return str(request.state.conversation_id)

        # For webhook requests, we'll need to parse the body
        # This is handled in the webhook endpoint itself
        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response: HTTP response
        """
        # Check if this path should be rate limited
        if not self._should_rate_limit(request.url.path):
            return await call_next(request)

        # For webhook endpoints, we need to extract conversation_id from body
        # We'll do a preliminary check here, but the main check happens in the endpoint
        conversation_id = self._extract_conversation_id(request)

        # If we can't extract conversation_id yet, let the request through
        # The endpoint will handle rate limiting after parsing the body
        if not conversation_id:
            response = await call_next(request)

            # Check if the endpoint set a rate limit flag
            if (
                hasattr(request.state, "check_rate_limit")
                and request.state.check_rate_limit
            ):
                conversation_id = getattr(request.state, "conversation_id", None)
                if conversation_id:
                    # Increment counter after successful processing
                    await self._increment_counter(conversation_id)

            return response

        # Check rate limit
        if not await self._check_rate_limit(conversation_id):
            logger.warning(
                "rate_limit_exceeded",
                conversation_id=conversation_id,
                path=request.url.path,
                max_requests=self.max_requests,
                window_seconds=self.window_seconds,
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.max_requests} requests per minute exceeded for this conversation",
                    "conversation_id": conversation_id,
                    "retry_after": self.window_seconds,
                },
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Window": str(self.window_seconds),
                },
            )

        # Increment counter
        await self._increment_counter(conversation_id)

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        remaining = await self._get_remaining_requests(conversation_id)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.window_seconds)

        return response

    async def _check_rate_limit(self, conversation_id: str) -> bool:
        """
        Check if request is within rate limit.

        Args:
            conversation_id: Conversation identifier

        Returns:
            bool: True if within limit, False if exceeded
        """
        try:
            key = self._get_rate_limit_key(conversation_id)
            current_count = await self.redis_client.get_value(key, deserialize=False)

            if current_count is None:
                return True

            count = int(current_count)
            return count < self.max_requests

        except Exception as e:
            logger.error(
                "rate_limit_check_failed", conversation_id=conversation_id, error=str(e)
            )
            # On error, allow the request (fail open)
            return True

    async def _increment_counter(self, conversation_id: str) -> None:
        """
        Increment rate limit counter for conversation.

        Args:
            conversation_id: Conversation identifier
        """
        try:
            key = self._get_rate_limit_key(conversation_id)

            await self.redis_client.ensure_initialized()
            client = self.redis_client.client

            # Increment counter
            current = await client.incr(key)

            # Set expiry on first increment
            if current == 1:
                await client.expire(key, self.window_seconds)

            logger.debug(
                "rate_limit_counter_incremented",
                conversation_id=conversation_id,
                count=current,
                max_requests=self.max_requests,
            )

        except Exception as e:
            logger.error(
                "rate_limit_increment_failed",
                conversation_id=conversation_id,
                error=str(e),
            )

    async def _get_remaining_requests(self, conversation_id: str) -> int:
        """
        Get remaining requests in current window.

        Args:
            conversation_id: Conversation identifier

        Returns:
            int: Number of remaining requests
        """
        try:
            key = self._get_rate_limit_key(conversation_id)
            current_count = await self.redis_client.get_value(key, deserialize=False)

            if current_count is None:
                return self.max_requests

            count = int(current_count)
            remaining = max(0, self.max_requests - count)
            return remaining

        except Exception as e:
            logger.error(
                "rate_limit_remaining_check_failed",
                conversation_id=conversation_id,
                error=str(e),
            )
            return self.max_requests


async def check_conversation_rate_limit(conversation_id: str) -> tuple[bool, int]:
    """
    Helper function to check rate limit for a conversation.
    Can be called directly from endpoints.

    Args:
        conversation_id: Conversation identifier

    Returns:
        tuple: (is_allowed, remaining_requests)
    """
    try:
        current_minute = int(time.time() / 60)
        key = f"ratelimit:{conversation_id}:{current_minute}"

        redis_client = get_redis_client()
        current_count = await redis_client.get_value(key, deserialize=False)

        if current_count is None:
            count = 0
        else:
            count = int(current_count)

        is_allowed = count < settings.max_requests_per_minute
        remaining = max(0, settings.max_requests_per_minute - count)

        return is_allowed, remaining

    except Exception as e:
        logger.error(
            "rate_limit_check_helper_failed",
            conversation_id=conversation_id,
            error=str(e),
        )
        # On error, allow the request
        return True, settings.max_requests_per_minute


async def increment_conversation_rate_limit(conversation_id: str) -> None:
    """
    Helper function to increment rate limit counter for a conversation.
    Should be called after successful request processing.

    Args:
        conversation_id: Conversation identifier
    """
    try:
        current_minute = int(time.time() / 60)
        key = f"ratelimit:{conversation_id}:{current_minute}"

        redis_client = get_redis_client()
        await redis_client.ensure_initialized()
        client = redis_client.client

        # Increment counter
        current = await client.incr(key)

        # Set expiry on first increment (60 seconds)
        if current == 1:
            await client.expire(key, 60)

        logger.debug(
            "rate_limit_incremented", conversation_id=conversation_id, count=current
        )

    except Exception as e:
        logger.error(
            "rate_limit_increment_helper_failed",
            conversation_id=conversation_id,
            error=str(e),
        )

