"""Async retry utilities with exponential backoff."""

from __future__ import annotations

import asyncio
from functools import wraps
from typing import Any, Awaitable, Callable, Iterable, Tuple


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Retry decorator for async callables with exponential backoff."""

    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: BaseException | None = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:  # type: ignore[arg-type]
                    last_exception = exc
                    if attempt >= max_attempts - 1:
                        break
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            if last_exception is not None:
                raise last_exception
            return None

        return wrapper

    return decorator


__all__ = ["async_retry"]
