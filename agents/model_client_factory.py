"""
Model Client Factory for AutoGen agents with Semantic Kernel integration.

This module provides a centralized factory for creating LLM model clients,
eliminating code duplication across all agents.

Supports:
- xAI Grok via OpenAI-compatible API
- Google Gemini via GoogleAI connector
- OpenAI (fallback)

Usage:
    from agents.model_client_factory import create_model_client
    from config.settings import settings
    
    llm_config = settings.get_llm_config()
    model_client = create_model_client(llm_config)
    
    agent = AssistantAgent(
        name="my_agent",
        model_client=model_client,
        system_message="..."
    )
"""

import logging
from typing import Dict, Any
from openai import AsyncOpenAI
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
from autogen_core.models import ModelInfo

from semantic_kernel import Kernel
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.connectors.ai.google.google_ai import (
    GoogleAIChatCompletion,
    GoogleAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)

logger = logging.getLogger(__name__)


def create_model_client(llm_config: Dict[str, Any]) -> SKChatCompletionAdapter:
    """
    Create Semantic Kernel model client based on LLM configuration.
    
    Args:
        llm_config: Configuration dictionary with keys:
            - provider: "xai" | "gemini" | "openai"
            - api_key: API key for the provider
            - model: Model name (e.g., "grok-beta", "gemini-2.0-flash-exp")
            - temperature: Optional temperature (default: 0.7)
            - max_tokens: Optional max tokens (default: 2048)
            - timeout: Optional timeout in seconds (default: 10)
            - base_url: Optional base URL for OpenAI-compatible APIs
    
    Returns:
        SKChatCompletionAdapter: Configured model client for AutoGen
    
    Raises:
        ValueError: If provider is unsupported or required config is missing
    
    Examples:
        >>> config = {
        ...     "provider": "xai",
        ...     "api_key": "xai-...",
        ...     "model": "grok-beta",
        ...     "base_url": "https://api.x.ai/v1"
        ... }
        >>> client = create_model_client(config)
    """
    provider = llm_config.get("provider", "").lower()
    api_key = llm_config.get("api_key")
    model = llm_config.get("model")
    temperature = llm_config.get("temperature", 0.7)
    max_tokens = llm_config.get("max_tokens", 2048)
    timeout = llm_config.get("timeout", 10)
    base_url = llm_config.get("base_url")

    if not provider:
        raise ValueError("LLM provider not specified in config")
    if not api_key:
        raise ValueError(f"API key not provided for provider '{provider}'")
    if not model:
        raise ValueError(f"Model name not specified for provider '{provider}'")

    logger.info(f"Creating model client: provider={provider}, model={model}")

    if provider == "gemini":
        return _create_gemini_client(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider in ("xai", "openai"):
        return _create_openai_compatible_client(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported: 'xai', 'gemini', 'openai'"
        )


def _create_gemini_client(
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> SKChatCompletionAdapter:
    """Create Gemini model client using GoogleAI connector."""
    kernel = Kernel(memory=NullMemory())
    
    service_id = f"gemini_{model}"
    kernel.add_service(
        GoogleAIChatCompletion(
            service_id=service_id,
            ai_model_id=model,
            api_key=api_key,
        )
    )

    execution_settings = GoogleAIChatPromptExecutionSettings(
        service_id=service_id,
        ai_model_id=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    model_client = SKChatCompletionAdapter(
        service_id=service_id,
        kernel=kernel,
        execution_settings=execution_settings,
    )

    logger.info(
        f"Gemini client created: model={model}, temp={temperature}, "
        f"max_tokens={max_tokens}"
    )

    return model_client


def _create_openai_compatible_client(
    provider: str,
    api_key: str,
    model: str,
    base_url: str | None,
    temperature: float,
    max_tokens: int,
    timeout: int,
) -> SKChatCompletionAdapter:
    """Create OpenAI-compatible client (for xAI Grok, OpenAI, etc.)."""
    async_client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
    )

    kernel = Kernel(memory=NullMemory())
    
    service_id = f"{provider}_{model}"
    kernel.add_service(
        OpenAIChatCompletion(
            service_id=service_id,
            ai_model_id=model,
            async_client=async_client,
        )
    )

    execution_settings = OpenAIChatPromptExecutionSettings(
        service_id=service_id,
        ai_model_id=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    model_client = SKChatCompletionAdapter(
        service_id=service_id,
        kernel=kernel,
        execution_settings=execution_settings,
    )

    logger.info(
        f"{provider.upper()} client created: model={model}, temp={temperature}, "
        f"max_tokens={max_tokens}, base_url={base_url}"
    )

    return model_client
