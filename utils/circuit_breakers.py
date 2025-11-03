"""
Centralized circuit breaker definitions for external integrations.

These breakers guard access to third-party services and critical
infrastructure components. They are intentionally lightweight so they
can be reused across the codebase without introducing tight coupling.
"""

import logging
from typing import Any

from pybreaker import CircuitBreaker, CircuitBreakerError, CircuitBreakerListener

logger = logging.getLogger(__name__)


class _LoggingCircuitBreakerListener(CircuitBreakerListener):
    """Logs circuit breaker state changes and failures."""

    def state_change(self, cb: CircuitBreaker, old_state: str, new_state: str) -> None:
        logger.warning(
            "Circuit breaker state changed",
            extra={
                "breaker": cb.name,
                "old_state": old_state,
                "new_state": new_state,
            },
        )

    def failure(self, cb: CircuitBreaker, exc: BaseException) -> None:
        logger.error(
            "Circuit breaker recorded failure",
            extra={"breaker": cb.name, "error": str(exc)},
        )


_listener = _LoggingCircuitBreakerListener()


calendar_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    name="calendar_api",
    listeners=[_listener],
)

supabase_breaker = CircuitBreaker(
    fail_max=8,
    reset_timeout=30,
    name="supabase",
    listeners=[_listener],
)

redis_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=20,
    name="redis",
    listeners=[_listener],
)

chatwoot_breaker = CircuitBreaker(
    fail_max=6,
    reset_timeout=45,
    name="chatwoot",
    listeners=[_listener],
)


__all__ = [
    "calendar_breaker",
    "supabase_breaker",
    "redis_breaker",
    "chatwoot_breaker",
    "CircuitBreakerError",
]
