import os

import pytest

_REQUIRED_ENV = {
    "SUPABASE_URL": "https://example.supabase.co",
    "SUPABASE_KEY": "test-supabase-key",
    "REDIS_URL": "redis://localhost:6379/0",
    "CHATWOOT_API_URL": "https://chatwoot.example.com",
    "CHATWOOT_ACCOUNT_ID": "1",
    "CHATWOOT_API_TOKEN": "test-chatwoot-token",
}

for _env_key, _env_value in _REQUIRED_ENV.items():
    os.environ.setdefault(_env_key, _env_value)

from agents.agent_factory import AgentFactory
from config.settings import settings


def _base_llm_config():
    return {
        "provider": "gemini",
        "api_key": "gemini-key",
        "model": "gemini-2.0-flash",
        "temperature": 0.6,
        "max_tokens": 2048,
        "timeout": 12,
    }


def test_agent_factory_prefers_xai_for_specialized_agents(monkeypatch):
    base_config = _base_llm_config()
    monkeypatch.setattr(
        settings.__class__,
        "get_llm_config",
        lambda self: base_config.copy(),
        raising=False,
    )
    monkeypatch.setattr(settings, "xai_api_key", "xai-key", raising=False)
    monkeypatch.setattr(settings, "xai_model", "grok-beta", raising=False)
    monkeypatch.setattr(settings, "xai_base_url", "https://api.x.ai/v1", raising=False)
    monkeypatch.setattr(settings, "response_timeout_seconds", 25, raising=False)

    captured = {}

    def fake_create_faq_agent(config, *args, **kwargs):
        captured["faq"] = config
        return "faq-agent"

    def fake_create_scheduler_agent(config, *args, **kwargs):
        captured["scheduler"] = config
        return "scheduler-agent"

    monkeypatch.setattr(
        "agents.agent_factory.create_faq_agent", fake_create_faq_agent, raising=False
    )
    monkeypatch.setattr(
        "agents.agent_factory.create_scheduler_agent",
        fake_create_scheduler_agent,
        raising=False,
    )

    factory = AgentFactory()

    # Ensure default config is returned as a defensive copy
    default_one = factory.default_llm_config
    default_one["provider"] = "mutated-provider"
    assert factory.default_llm_config["provider"] == base_config["provider"]

    factory.create_faq()
    factory.create_scheduler()

    assert captured["faq"]["provider"] == "xai"
    assert captured["scheduler"]["provider"] == "xai"
    assert captured["faq"]["base_url"] == settings.xai_base_url
    assert captured["scheduler"]["timeout"] == settings.response_timeout_seconds


def test_agent_factory_uses_default_when_xai_missing(monkeypatch):
    base_config = _base_llm_config()
    monkeypatch.setattr(
        settings.__class__,
        "get_llm_config",
        lambda self: base_config.copy(),
        raising=False,
    )
    monkeypatch.setattr(settings, "xai_api_key", None, raising=False)
    monkeypatch.setattr(settings, "xai_model", "unused-model", raising=False)
    monkeypatch.setattr(settings, "xai_base_url", None, raising=False)

    captured = {}

    def fake_create_faq_agent(config, *args, **kwargs):
        captured["faq"] = config
        return "faq-agent"

    monkeypatch.setattr(
        "agents.agent_factory.create_faq_agent", fake_create_faq_agent, raising=False
    )

    factory = AgentFactory()
    factory.create_faq()

    assert captured["faq"]["provider"] == base_config["provider"]
    assert captured["faq"]["api_key"] == base_config["api_key"]
