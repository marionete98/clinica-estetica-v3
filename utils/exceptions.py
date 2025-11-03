"""Custom exception hierarchy for agent and repository errors."""


class AgentError(Exception):
    """Base exception for agent-related failures."""


class LLMTimeoutError(AgentError):
    """Raised when an LLM request exceeds the configured timeout."""


class LLMRateLimitError(AgentError):
    """Raised when the upstream model returns a rate-limit error."""


class RepositoryError(AgentError):
    """Raised when repository operations fail."""


class CacheError(AgentError):
    """Raised when cache operations fail."""


class ValidationError(AgentError):
    """Raised when user-provided inputs fail validation checks."""


__all__ = [
    "AgentError",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "RepositoryError",
    "CacheError",
    "ValidationError",
]
