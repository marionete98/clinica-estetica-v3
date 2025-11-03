"""Type-safe configuration structures and constants for agent LLMs."""

from typing import TypedDict, Literal, Optional


LLMProvider = Literal["xai", "gemini", "openai"]


class LLMConfig(TypedDict, total=False):
    """
    Type-safe LLM configuration dictionary.
    
    Attributes:
        provider: LLM provider selection
        api_key: API key for the provider
        model: Model name/identifier
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response
        timeout: Request timeout in seconds
        base_url: Optional base URL for OpenAI-compatible APIs
    
    Examples:
        >>> config: LLMConfig = {
        ...     "provider": "xai",
        ...     "api_key": "xai-...",
        ...     "model": "grok-beta",
        ...     "temperature": 0.7,
        ...     "max_tokens": 2048,
        ...     "timeout": 10,
        ...     "base_url": "https://api.x.ai/v1"
        ... }
    """
    provider: LLMProvider
    api_key: str
    model: str
    temperature: float
    max_tokens: int
    timeout: int
    base_url: Optional[str]


class AgentConstants:
    """
    Centralized constants for agent configuration.
    
    All magic numbers and hardcoded values should be defined here
    to improve maintainability and configurability.
    """
    
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 2048
    DEFAULT_TIMEOUT: int = 10
    
    FAQ_CACHE_TTL_SECONDS: int = 3600
    FAQ_CACHE_MAX_SIZE: int = 100
    
    CONTEXT_WINDOW_SUPERVISOR: int = 3
    CONTEXT_WINDOW_INTAKE: int = 3
    CONTEXT_WINDOW_FAQ: int = 4
    CONTEXT_WINDOW_SCHEDULER: int = 6
    CONTEXT_WINDOW_ESCALATION: int = 10
    
    MAX_TOOL_CALLS_PER_SESSION: int = 3
    MAX_CONTEXT_MESSAGES: int = 20
    
    MESSAGE_DEDUP_TTL_SECONDS: int = 300
    MESSAGE_PROCESSING_DELAY_SECONDS: int = 7
    
    SCHEDULER_MAX_SLOTS_DISPLAY: int = 5


def create_llm_config(
    provider: LLMProvider,
    api_key: str,
    model: str,
    temperature: float = AgentConstants.DEFAULT_TEMPERATURE,
    max_tokens: int = AgentConstants.DEFAULT_MAX_TOKENS,
    timeout: int = AgentConstants.DEFAULT_TIMEOUT,
    base_url: Optional[str] = None,
) -> LLMConfig:
    """
    Create a type-safe LLM configuration.
    
    Args:
        provider: LLM provider
        api_key: API key
        model: Model name
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        timeout: Request timeout
        base_url: Optional base URL
    
    Returns:
        LLMConfig: Type-safe configuration dictionary
    
    Examples:
        >>> config = create_llm_config(
        ...     provider="xai",
        ...     api_key="xai-...",
        ...     model="grok-beta",
        ...     base_url="https://api.x.ai/v1"
        ... )
    """
    config: LLMConfig = {
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout": timeout,
    }
    
    if base_url:
        config["base_url"] = base_url
    
    return config
