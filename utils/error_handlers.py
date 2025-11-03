"""
Error handlers module with retry logic and fallback responses.
Implements retry strategies for external services and timeout handling for LLM calls.
"""

import time
import asyncio
from typing import Any, Callable, Optional, TypeVar, ParamSpec
from functools import wraps
from enum import Enum
import structlog
from httpx import HTTPStatusError, RequestError, TimeoutException

logger = structlog.get_logger(__name__)

# Type variables for generic decorators
P = ParamSpec('P')
T = TypeVar('T')


class ErrorType(str, Enum):
    """Error types for categorization."""
    SYSTEM_BUSY = "system_busy"
    SERVICE_UNAVAILABLE = "service_unavailable"
    UNCLEAR_REQUEST = "unclear_request"
    NO_SLOTS = "no_slots"
    POLICY_VIOLATION = "policy_violation"
    LLM_TIMEOUT = "llm_timeout"
    CHATWOOT_ERROR = "chatwoot_error"
    SUPABASE_ERROR = "supabase_error"
    REDIS_ERROR = "redis_error"
    UNKNOWN_ERROR = "unknown_error"


# Fallback response templates
ERROR_RESPONSES = {
    ErrorType.SYSTEM_BUSY: "Desculpe, estou com alta demanda no momento. Pode tentar novamente em alguns segundos?",
    ErrorType.SERVICE_UNAVAILABLE: "Estou com dificuldades técnicas temporárias. Vou transferir você para um atendente humano.",
    ErrorType.UNCLEAR_REQUEST: "Desculpe, não entendi completamente. Você pode reformular sua pergunta?",
    ErrorType.NO_SLOTS: "Não encontrei horários disponíveis para {service} em {date_range}. O próximo horário disponível é {next_slot}. Deseja agendar?",
    ErrorType.POLICY_VIOLATION: "Infelizmente, cancelamentos de {service_type} precisam ser feitos com {hours}h de antecedência. Posso transferir você para nossa equipe avaliar sua situação?",
    ErrorType.LLM_TIMEOUT: "Estou processando sua solicitação, um momento por favor...",
    ErrorType.CHATWOOT_ERROR: "Tive um problema ao enviar a mensagem. Vou tentar novamente.",
    ErrorType.SUPABASE_ERROR: "Tive um problema ao acessar os dados. Tentando novamente...",
    ErrorType.REDIS_ERROR: "Continuando sem histórico da conversa anterior.",
    ErrorType.UNKNOWN_ERROR: "Desculpe, ocorreu um erro inesperado. Vou transferir você para um atendente humano.",
}


def get_fallback_response(error_type: ErrorType, **kwargs) -> str:
    """
    Get fallback response for an error type.
    
    Args:
        error_type: Type of error
        **kwargs: Template variables for formatting
    
    Returns:
        str: Formatted fallback response
    """
    template = ERROR_RESPONSES.get(error_type, ERROR_RESPONSES[ErrorType.UNKNOWN_ERROR])
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        logger.warning(
                            "retry_attempt",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            error=str(e),
                            retry_delay=delay
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            "retry_exhausted",
                            function=func.__name__,
                            attempts=max_retries,
                            error=str(e)
                        )
            
            # Raise the last exception if all retries failed
            if last_exception:
                raise last_exception
            
            # This should never happen, but satisfy type checker
            raise RuntimeError("Unexpected retry logic error")
        
        return wrapper
    return decorator


def async_retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Async decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry
    
    Returns:
        Decorated async function with retry logic
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        logger.warning(
                            "async_retry_attempt",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            error=str(e),
                            retry_delay=delay
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            "async_retry_exhausted",
                            function=func.__name__,
                            attempts=max_retries,
                            error=str(e)
                        )
            
            # Raise the last exception if all retries failed
            if last_exception:
                raise last_exception
            
            # This should never happen, but satisfy type checker
            raise RuntimeError("Unexpected retry logic error")
        
        return wrapper
    return decorator


# Specific retry decorators for different services

def retry_chatwoot(func: Callable[P, T]) -> Callable[P, T]:
    """
    Retry decorator specifically for Chatwoot API calls.
    Retries 3 times with exponential backoff on HTTP and request errors.
    """
    return retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(HTTPStatusError, RequestError, TimeoutException)
    )(func)


def retry_supabase(func: Callable[P, T]) -> Callable[P, T]:
    """
    Retry decorator specifically for Supabase operations.
    Retries 3 times with exponential backoff on connection and timeout errors.
    """
    return retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(ConnectionError, TimeoutError, Exception)
    )(func)


def timeout_llm_call(timeout_seconds: int):
    """
    Decorator to add timeout to LLM calls.
    
    Args:
        timeout_seconds: Timeout in seconds (10s for Gemini, 15s for Grok)
    
    Returns:
        Decorated function with timeout
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"LLM call timed out after {timeout_seconds} seconds")
            
            # Set the signal handler and alarm
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Disable the alarm
                return result
            except TimeoutError as e:
                logger.error(
                    "llm_call_timeout",
                    function=func.__name__,
                    timeout=timeout_seconds,
                    error=str(e)
                )
                raise
            finally:
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator


def async_timeout_llm_call(timeout_seconds: int):
    """
    Async decorator to add timeout to LLM calls.
    
    Args:
        timeout_seconds: Timeout in seconds (10s for Gemini, 15s for Grok)
    
    Returns:
        Decorated async function with timeout
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError as e:
                logger.error(
                    "async_llm_call_timeout",
                    function=func.__name__,
                    timeout=timeout_seconds,
                    error=str(e)
                )
                raise TimeoutError(f"LLM call timed out after {timeout_seconds} seconds")
        
        return wrapper
    return decorator


class LLMTimeoutHandler:
    """Handler for LLM timeout scenarios with provider-specific timeouts."""
    
    # Timeout values per provider (in seconds)
    GEMINI_TIMEOUT = 10
    GROK_TIMEOUT = 15
    
    @classmethod
    def get_timeout(cls, provider: str) -> int:
        """
        Get timeout value for a specific LLM provider.
        
        Args:
            provider: LLM provider name ('gemini' or 'xai')
        
        Returns:
            int: Timeout in seconds
        """
        if provider.lower() == "gemini":
            return cls.GEMINI_TIMEOUT
        elif provider.lower() in ("xai", "grok"):
            return cls.GROK_TIMEOUT
        else:
            # Default to Grok timeout for unknown providers
            return cls.GROK_TIMEOUT
    
    @classmethod
    def handle_timeout(cls, provider: str, conversation_id: str) -> str:
        """
        Handle LLM timeout and return fallback response.
        
        Args:
            provider: LLM provider name
            conversation_id: Conversation identifier
        
        Returns:
            str: Fallback response message
        """
        logger.error(
            "llm_timeout_handled",
            provider=provider,
            conversation_id=conversation_id,
            timeout=cls.get_timeout(provider)
        )
        
        return get_fallback_response(ErrorType.LLM_TIMEOUT)


class ServiceErrorHandler:
    """Handler for external service errors with graceful degradation."""
    
    @staticmethod
    def handle_chatwoot_error(error: Exception, conversation_id: str) -> str:
        """
        Handle Chatwoot API errors.
        
        Args:
            error: Exception that occurred
            conversation_id: Conversation identifier
        
        Returns:
            str: Fallback response message
        """
        logger.error(
            "chatwoot_error_handled",
            conversation_id=conversation_id,
            error=str(error),
            error_type=type(error).__name__
        )
        
        return get_fallback_response(ErrorType.CHATWOOT_ERROR)
    
    @staticmethod
    def handle_supabase_error(error: Exception, operation: str) -> Optional[Any]:
        """
        Handle Supabase errors with graceful degradation.
        
        Args:
            error: Exception that occurred
            operation: Operation that failed
        
        Returns:
            Optional fallback data or None
        """
        logger.error(
            "supabase_error_handled",
            operation=operation,
            error=str(error),
            error_type=type(error).__name__
        )
        
        # Return None to indicate failure, caller should handle gracefully
        return None
    
    @staticmethod
    def handle_redis_error(error: Exception, conversation_id: str) -> list:
        """
        Handle Redis errors by returning empty context.
        
        Args:
            error: Exception that occurred
            conversation_id: Conversation identifier
        
        Returns:
            list: Empty context list
        """
        logger.warning(
            "redis_error_handled",
            conversation_id=conversation_id,
            error=str(error),
            error_type=type(error).__name__,
            fallback="operating_without_context"
        )
        
        # Return empty context for graceful degradation
        return []


class ErrorRecoveryStrategy:
    """Strategies for recovering from different error scenarios."""
    
    @staticmethod
    def should_escalate(error_count: int, error_type: ErrorType) -> bool:
        """
        Determine if conversation should be escalated to human.
        
        Args:
            error_count: Number of consecutive errors
            error_type: Type of error
        
        Returns:
            bool: True if should escalate, False otherwise
        """
        # Escalate after 3 consecutive errors
        if error_count >= 3:
            return True
        
        # Escalate immediately for critical errors
        critical_errors = {
            ErrorType.SERVICE_UNAVAILABLE,
            ErrorType.UNKNOWN_ERROR
        }
        
        if error_type in critical_errors:
            return True
        
        return False
    
    @staticmethod
    def get_recovery_action(error_type: ErrorType) -> str:
        """
        Get recommended recovery action for an error type.
        
        Args:
            error_type: Type of error
        
        Returns:
            str: Recovery action description
        """
        recovery_actions = {
            ErrorType.SYSTEM_BUSY: "retry_after_delay",
            ErrorType.SERVICE_UNAVAILABLE: "escalate_to_human",
            ErrorType.UNCLEAR_REQUEST: "request_clarification",
            ErrorType.NO_SLOTS: "suggest_alternatives",
            ErrorType.POLICY_VIOLATION: "explain_policy_and_offer_escalation",
            ErrorType.LLM_TIMEOUT: "use_fallback_response_and_escalate",
            ErrorType.CHATWOOT_ERROR: "retry_with_backoff",
            ErrorType.SUPABASE_ERROR: "retry_with_backoff",
            ErrorType.REDIS_ERROR: "continue_without_context",
            ErrorType.UNKNOWN_ERROR: "escalate_to_human",
        }
        
        return recovery_actions.get(error_type, "escalate_to_human")


def safe_execute(
    func: Callable[P, T],
    fallback_value: T,
    error_handler: Optional[Callable[[Exception], None]] = None
) -> Callable[P, T]:
    """
    Decorator to safely execute a function with fallback value on error.
    
    Args:
        func: Function to execute
        fallback_value: Value to return on error
        error_handler: Optional error handler function
    
    Returns:
        Decorated function that returns fallback_value on error
    """
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                "safe_execute_error",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__
            )
            
            if error_handler:
                error_handler(e)
            
            return fallback_value
    
    return wrapper
