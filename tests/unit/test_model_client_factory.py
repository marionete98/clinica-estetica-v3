"""Unit tests for the model client factory."""

from __future__ import annotations

import pytest

import agents.model_client_factory as factory


@pytest.mark.parametrize(
    "provider,helper_name",
    [
        ("gemini", "_create_gemini_client"),
        ("xai", "_create_openai_compatible_client"),
    ],
)
def test_create_model_client_delegates_to_helper(monkeypatch: pytest.MonkeyPatch, provider: str, helper_name: str) -> None:
    captured = {}

    def fake_helper(**kwargs):  # type: ignore[unused-argument]
        captured.update(kwargs)
        return f"client-{provider}"

    monkeypatch.setattr(factory, helper_name, fake_helper)

    config = {
        "provider": provider,
        "api_key": "key",
        "model": "model-name",
        "temperature": 0.5,
        "max_tokens": 512,
        "timeout": 15,
        "base_url": "https://example.com",
    }

    client = factory.create_model_client(config)

    assert client == f"client-{provider}"
    assert captured["model"] == "model-name"


def test_create_model_client_rejects_missing_api_key() -> None:
    with pytest.raises(ValueError):
        factory.create_model_client({"provider": "xai", "model": "grok"})


def test_create_model_client_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError):
        factory.create_model_client(
            {"provider": "unknown", "api_key": "key", "model": "model"}
        )
