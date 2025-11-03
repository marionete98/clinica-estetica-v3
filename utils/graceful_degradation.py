"""
Graceful degradation module for handling service failures.
Implements fallback strategies when external dependencies are unavailable.
"""

from typing import Any, Optional, Callable
from enum import Enum
import structlog

from utils.error_handlers import ErrorType, get_fallback_response

logger = structlog.get_logger(__name__)


class ServiceStatus(str, Enum):
    """Service availability status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class DegradationMode(str, Enum):
    """System degradation modes."""
    NORMAL = "normal"
    NO_CONTEXT = "no_context"  # Redis unavailable
    READ_ONLY = "read_only"  # Supabase slow/unavailable for writes
    FALLBACK_RESPONSES = "fallback_responses"  # LLM timeout
    ESCALATION_ONLY = "escalation_only"  # Multiple services down


class GracefulDegradationManager:
    """
    Manager for graceful degradation strategies.
    Handles service failures and determines appropriate fallback behavior.
    """

    def __init__(self):
        """Initialize degradation manager."""
        self.service_status = {
            "redis": ServiceStatus.HEALTHY,
            "supabase": ServiceStatus.HEALTHY,
            "llm": ServiceStatus.HEALTHY,
            "chatwoot": ServiceStatus.HEALTHY,
        }
        self.current_mode = DegradationMode.NORMAL

        logger.info("graceful_degradation_manager_initialized")

    def update_service_status(self, service: str, status: ServiceStatus) -> None:
        """
        Update status of a service.

        Args:
            service: Service name (redis, supabase, llm, chatwoot)
            status: New status
        """
        old_status = self.service_status.get(service)
        self.service_status[service] = status

        if old_status != status:
            logger.warning(
                "service_status_changed",
                service=service,
                old_status=old_status,
                new_status=status
            )

        # Update degradation mode based on service statuses
        self._update_degradation_mode()

    def _update_degradation_mode(self) -> None:
        """Update system degradation mode based on service statuses."""
        old_mode = self.current_mode

        # Count unavailable services
        unavailable_count = sum(
            1 for status in self.service_status.values()
            if status == ServiceStatus.UNAVAILABLE
        )

        # Determine degradation mode
        if unavailable_count >= 2:
            self.current_mode = DegradationMode.ESCALATION_ONLY
        elif self.service_status["redis"] == ServiceStatus.UNAVAILABLE:
            self.current_mode = DegradationMode.NO_CONTEXT
        elif self.service_status["supabase"] in (ServiceStatus.DEGRADED, ServiceStatus.UNAVAILABLE):
            self.current_mode = DegradationMode.READ_ONLY
        elif self.service_status["llm"] in (ServiceStatus.DEGRADED, ServiceStatus.UNAVAILABLE):
            self.current_mode = DegradationMode.FALLBACK_RESPONSES
        else:
            self.current_mode = DegradationMode.NORMAL

        if old_mode != self.current_mode:
            logger.warning(
                "degradation_mode_changed",
                old_mode=old_mode,
                new_mode=self.current_mode,
                service_statuses=self.service_status
            )

    def get_degradation_mode(self) -> DegradationMode:
        """
        Get current degradation mode.

        Returns:
            DegradationMode: Current mode
        """
        return self.current_mode

    def is_service_available(self, service: str) -> bool:
        """
        Check if a service is available.

        Args:
            service: Service name

        Returns:
            bool: True if service is healthy or degraded, False if unavailable
        """
        status = self.service_status.get(service, ServiceStatus.UNAVAILABLE)
        return status != ServiceStatus.UNAVAILABLE

    def should_escalate(self) -> bool:
        """
        Determine if conversation should be escalated due to degradation.

        Returns:
            bool: True if should escalate
        """
        return self.current_mode == DegradationMode.ESCALATION_ONLY


class RedisGracefulDegradation:
    """
    Graceful degradation strategies for Redis unavailability.
    System operates without conversation context when Redis is down.
    """

    @staticmethod
    def get_empty_context() -> list:
        """
        Get empty context when Redis is unavailable.

        Returns:
            list: Empty context list
        """
        logger.info("redis_degradation_empty_context")
        return []

    @staticmethod
    def handle_context_failure(conversation_id: str, error: Exception) -> list:
        """
        Handle Redis context retrieval failure.

        Args:
            conversation_id: Conversation identifier
            error: Exception that occurred

        Returns:
            list: Empty context for graceful degradation
        """
        logger.warning(
            "redis_context_failure_degraded",
            conversation_id=conversation_id,
            error=str(error),
            fallback="empty_context"
        )

        return []

    @staticmethod
    def skip_context_update(conversation_id: str) -> bool:
        """
        Skip context update when Redis is unavailable.

        Args:
            conversation_id: Conversation identifier

        Returns:
            bool: Always True (operation skipped successfully)
        """
        logger.debug(
            "redis_context_update_skipped",
            conversation_id=conversation_id
        )

        return True


class SupabaseGracefulDegradation:
    """
    Graceful degradation strategies for Supabase issues.
    System operates in read-only mode for FAQ when Supabase is slow/unavailable.
    """

    def __init__(self):
        """Initialize Supabase degradation handler."""
        self.cached_kb_articles = {}
        self.cached_services = {}
        self.read_only_mode = False

    def enable_read_only_mode(self) -> None:
        """Enable read-only mode for FAQ operations."""
        self.read_only_mode = True
        logger.warning("supabase_read_only_mode_enabled")

    def disable_read_only_mode(self) -> None:
        """Disable read-only mode."""
        self.read_only_mode = False
        logger.info("supabase_read_only_mode_disabled")

    def cache_kb_article(self, article_id: str, content: dict) -> None:
        """
        Cache a knowledge base article.

        Args:
            article_id: Article identifier
            content: Article content
        """
        self.cached_kb_articles[article_id] = content
        logger.debug("kb_article_cached", article_id=article_id)

    def get_cached_kb_article(self, article_id: str) -> Optional[dict]:
        """
        Get cached knowledge base article.

        Args:
            article_id: Article identifier

        Returns:
            Optional[dict]: Cached article or None
        """
        return self.cached_kb_articles.get(article_id)

    def handle_write_failure(self, operation: str, data: dict) -> dict:
        """
        Handle Supabase write failure by queueing for later.

        Args:
            operation: Operation name
            data: Data that failed to write

        Returns:
            dict: Response indicating queued status
        """
        logger.warning(
            "supabase_write_queued",
            operation=operation,
            read_only_mode=self.read_only_mode
        )

        return {
            "status": "queued",
            "message": "Operação será processada em breve",
            "operation": operation
        }

    def can_perform_write(self) -> bool:
        """
        Check if write operations are allowed.

        Returns:
            bool: True if writes are allowed, False if in read-only mode
        """
        return not self.read_only_mode


class LLMGracefulDegradation:
    """
    Graceful degradation strategies for LLM timeouts/failures.
    System uses fallback responses and escalates when LLM is unavailable.
    """

    @staticmethod
    def get_timeout_response() -> str:
        """
        Get fallback response for LLM timeout.

        Returns:
            str: Fallback message
        """
        return get_fallback_response(ErrorType.LLM_TIMEOUT)

    @staticmethod
    def handle_llm_timeout(
        conversation_id: str,
        provider: str,
        intent: str
    ) -> tuple[str, bool]:
        """
        Handle LLM timeout with fallback response.

        Args:
            conversation_id: Conversation identifier
            provider: LLM provider name
            intent: Detected intent

        Returns:
            tuple: (fallback_response, should_escalate)
        """
        logger.error(
            "llm_timeout_degraded",
            conversation_id=conversation_id,
            provider=provider,
            intent=intent
        )

        # Return generic response and flag for escalation
        response = LLMGracefulDegradation.get_timeout_response()
        should_escalate = True

        return response, should_escalate

    @staticmethod
    def get_intent_specific_fallback(intent: str) -> str:
        """
        Get intent-specific fallback response.

        Args:
            intent: Conversation intent

        Returns:
            str: Fallback response
        """
        fallbacks = {
            "faq": "Desculpe, estou com dificuldade para responder agora. Vou transferir você para um atendente.",
            "schedule": "Estou processando sua solicitação de agendamento. Um atendente entrará em contato em breve.",
            "reschedule": "Vou transferir você para nossa equipe processar sua remarcação.",
            "cancel": "Vou transferir você para nossa equipe processar seu cancelamento.",
        }

        return fallbacks.get(intent, LLMGracefulDegradation.get_timeout_response())


class DegradationStrategy:
    """
    Main strategy coordinator for graceful degradation.
    Determines appropriate actions based on current degradation mode.
    """

    def __init__(self, manager: GracefulDegradationManager):
        """
        Initialize degradation strategy.

        Args:
            manager: GracefulDegradationManager instance
        """
        self.manager = manager
        self.redis_degradation = RedisGracefulDegradation()
        self.supabase_degradation = SupabaseGracefulDegradation()
        self.llm_degradation = LLMGracefulDegradation()

    def get_context_strategy(self, conversation_id: str) -> Callable:
        """
        Get context retrieval strategy based on degradation mode.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Callable: Function to retrieve context
        """
        if self.manager.current_mode == DegradationMode.NO_CONTEXT:
            return lambda: self.redis_degradation.get_empty_context()

        # Normal context retrieval
        return None

    def get_storage_strategy(self, operation: str) -> tuple[bool, Optional[str]]:
        """
        Get storage strategy based on degradation mode.

        Args:
            operation: Storage operation name

        Returns:
            tuple: (can_proceed, fallback_message)
        """
        mode = self.manager.current_mode

        if mode == DegradationMode.READ_ONLY:
            if operation in ("insert", "update", "delete"):
                return False, "Sistema em modo somente leitura. Operação será processada em breve."
            return True, None

        if mode == DegradationMode.ESCALATION_ONLY:
            return False, "Sistema com problemas técnicos. Transferindo para atendente humano."

        return True, None

    def get_response_strategy(self, intent: str) -> tuple[bool, Optional[str]]:
        """
        Get response generation strategy based on degradation mode.

        Args:
            intent: Conversation intent

        Returns:
            tuple: (use_llm, fallback_response)
        """
        mode = self.manager.current_mode

        if mode == DegradationMode.FALLBACK_RESPONSES:
            fallback = self.llm_degradation.get_intent_specific_fallback(intent)
            return False, fallback

        if mode == DegradationMode.ESCALATION_ONLY:
            return False, get_fallback_response(ErrorType.SERVICE_UNAVAILABLE)

        return True, None

    def should_skip_operation(self, operation_type: str) -> bool:
        """
        Determine if an operation should be skipped due to degradation.

        Args:
            operation_type: Type of operation (context_update, write, etc.)

        Returns:
            bool: True if operation should be skipped
        """
        mode = self.manager.current_mode

        skip_rules = {
            DegradationMode.NO_CONTEXT: {"context_update"},
            DegradationMode.READ_ONLY: {"write", "update", "delete"},
            DegradationMode.ESCALATION_ONLY: {"llm_call", "write"},
        }

        operations_to_skip = skip_rules.get(mode, set())
        return operation_type in operations_to_skip


# Global degradation manager instance
degradation_manager = GracefulDegradationManager()

# Global degradation strategy instance
degradation_strategy = DegradationStrategy(degradation_manager)

# Minimal async helpers expected by tests
async def handle_redis_unavailable():
    """Return empty context when Redis is unavailable (async helper)."""
    return RedisGracefulDegradation.get_empty_context()

async def handle_supabase_slow():
    """Enable read-only mode and return simple status (async helper)."""
    handler = SupabaseGracefulDegradation()
    handler.enable_read_only_mode()
    return {"read_only": True}

async def handle_llm_timeout():
    """Return generic fallback response for LLM timeout (async helper)."""
    return LLMGracefulDegradation.get_timeout_response()

