"""
Tests for configuration modules.
"""

import pytest
from unittest.mock import patch, MagicMock
from config.settings import Settings


def test_settings_xai_provider():
    """Test settings with xAI provider."""
    with patch.dict('os.environ', {
        'MODEL_PROVIDER': 'xai',
        'XAI_API_KEY': 'test-key',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key',
        'REDIS_URL': 'redis://localhost:6379',
        'CHATWOOT_API_URL': 'https://test.chatwoot.com',
        'CHATWOOT_ACCOUNT_ID': '123',
        'CHATWOOT_API_TOKEN': 'test-token',
        'CHATWOOT_WEBHOOK_TOKEN': 'test-token',
            'XAI_MODEL': 'grok-4-reasoning'
    }):
        settings = Settings()
        assert settings.model_provider == 'xai'
        
        llm_config = settings.get_llm_config()
        assert llm_config['provider'] == 'xai'
        assert llm_config['api_key'] == 'test-key'
        assert llm_config['model'] == 'grok-4-reasoning'


def test_settings_gemini_provider():
    """Test settings with Gemini provider."""
    with patch.dict('os.environ', {
        'MODEL_PROVIDER': 'gemini',
        'GEMINI_API_KEY': 'test-key',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key',
        'REDIS_URL': 'redis://localhost:6379',
        'CHATWOOT_API_URL': 'https://test.chatwoot.com',
        'CHATWOOT_ACCOUNT_ID': '123',
        'CHATWOOT_API_TOKEN': 'test-token',
        'CHATWOOT_WEBHOOK_TOKEN': 'test-token'
    }):
        settings = Settings()
        assert settings.model_provider == 'gemini'
        
        llm_config = settings.get_llm_config()
        assert llm_config['provider'] == 'gemini'
        assert llm_config['api_key'] == 'test-key'
        assert llm_config['model'] == 'gemini-2.5-flash'


def test_settings_missing_xai_key():
    """Test that missing xAI key raises error when xAI is selected."""
    with patch.dict('os.environ', {
        'MODEL_PROVIDER': 'xai',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key',
        'REDIS_URL': 'redis://localhost:6379',
        'CHATWOOT_API_URL': 'https://test.chatwoot.com',
        'CHATWOOT_ACCOUNT_ID': '123',
        'CHATWOOT_API_TOKEN': 'test-token',
        'CHATWOOT_WEBHOOK_TOKEN': 'test-token'
    }, clear=True):
        with pytest.raises(ValueError, match="XAI_API_KEY is required"):
            Settings().get_llm_config()


def test_settings_environment_properties():
    """Test environment property helpers."""
    with patch.dict('os.environ', {
        'MODEL_PROVIDER': 'xai',
        'XAI_API_KEY': 'test-key',
        'ENV': 'production',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key',
        'REDIS_URL': 'redis://localhost:6379',
        'CHATWOOT_API_URL': 'https://test.chatwoot.com',
        'CHATWOOT_ACCOUNT_ID': '123',
        'CHATWOOT_API_TOKEN': 'test-token',
        'CHATWOOT_WEBHOOK_TOKEN': 'test-token'
    }):
        settings = Settings()
        assert settings.is_production is True
        assert settings.is_development is False
