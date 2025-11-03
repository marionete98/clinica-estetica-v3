"""Unit tests for LLM configuration helpers."""

from __future__ import annotations

import pytest

from config.llm_config import AgentConstants, create_llm_config


def test_create_llm_config_populates_defaults() -> None:
    config = create_llm_config(provider="gemini", api_key="key", model="flash")

    assert config["temperature"] == AgentConstants.DEFAULT_TEMPERATURE
    assert config["max_tokens"] == AgentConstants.DEFAULT_MAX_TOKENS
    assert config["timeout"] == AgentConstants.DEFAULT_TIMEOUT
    assert "base_url" not in config


def test_create_llm_config_accepts_base_url() -> None:
    config = create_llm_config(
        provider="xai",
        api_key="key",
        model="grok-beta",
        base_url="https://api.x.ai/v1",
        temperature=0.4,
    )

    assert config["base_url"] == "https://api.x.ai/v1"
    assert config["temperature"] == 0.4


def test_create_llm_config_requires_provider() -> None:
    with pytest.raises(TypeError):
        create_llm_config()  # type: ignore[misc]
