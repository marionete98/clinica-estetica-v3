"""
Configuration module for Clinica Luana multi-agent scheduling system.
Loads and validates environment variables using pydantic-settings.
"""

import os
import sys
from typing import Literal, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from config.llm_config import LLMConfig, create_llm_config, AgentConstants


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=None if ("pytest" in sys.modules) else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================
    # LLM Configuration
    # ============================================
    model_provider: Literal["xai", "gemini"] = Field(
        default="xai",
        description="LLM provider selection: 'xai' for Grok or 'gemini' for Gemini",
    )

    # xAI Grok Configuration
    xai_api_key: Optional[str] = Field(default=None, description="xAI API key")
    xai_model: str = Field(default="grok-4-reasoning", description="xAI model name")
    xai_base_url: str = Field(
        default="https://api.x.ai/v1", description="xAI API base URL"
    )

    # Google Gemini Configuration
    gemini_api_key: Optional[str] = Field(
        default=None, description="Google Gemini API key"
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash", description="Gemini model name"
    )
    gemini_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        description="Gemini OpenAI-compatible API base URL",
    )

    # ============================================
    # Database Configuration
    # ============================================
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase service role key")
    supabase_jwt_secret: Optional[str] = Field(
        default=None, description="Supabase JWT secret"
    )

    # ============================================
    # Cache Configuration
    # ============================================
    redis_url: str = Field(..., description="Redis connection URL")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_host: Optional[str] = Field(default=None, description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")

    # ============================================
    # Chatwoot Configuration
    # ============================================
    chatwoot_api_url: str = Field(..., description="Chatwoot API base URL")
    chatwoot_account_id: str = Field(..., description="Chatwoot account ID")
    chatwoot_api_token: str = Field(..., description="Chatwoot API access token")
    chatwoot_webhook_token: Optional[str] = Field(
        default=None, description="Chatwoot webhook token for authentication"
    )
    chatwoot_finance_inbox_id: Optional[int] = Field(
        default=None, description="Chatwoot Inbox ID for Finance team (different WhatsApp number)"
    )
    chatwoot_finance_team_id: Optional[int] = Field(
        default=None, description="Chatwoot Team ID for Finance team"
    )
    chatwoot_finance_phone: Optional[str] = Field(
        default=None, description="Finance WhatsApp number for customer notification"
    )

    @field_validator("chatwoot_finance_inbox_id", "chatwoot_finance_team_id", mode="before")
    @classmethod
    def _empty_string_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    # ============================================
    # Calendar API Configuration
    # ============================================
    calendar_api_url: str = Field(
        default="https://clinica-luana-calendar-production.up.railway.app/api",
        description="Calendar API base URL",
    )
    calendar_api_timeout: int = Field(
        default=10, description="Calendar API request timeout in seconds"
    )

    # ============================================
    # Application Configuration
    # ============================================
    env: Literal["development", "staging", "production", "prod"] = Field(
        default="development", description="Application environment"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    port: int = Field(default=8000, description="Application port")
    app_version: str = Field(
        default="0.1.0", description="Semantic version for the FastAPI application"
    )

    # Agent Configuration
    max_tool_calls_per_session: int = Field(
        default=3, description="Maximum tool calls allowed per agent session"
    )
    response_timeout_seconds: int = Field(
        default=10, description="Timeout for LLM responses in seconds"
    )
    max_context_messages: int = Field(
        default=20,
        description="Maximum number of messages to keep in conversation context",
    )

    # Rate Limiting
    max_requests_per_minute: int = Field(
        default=100, description="Maximum requests per minute per conversation"
    )

    # Message Processing
    message_dedup_ttl_seconds: int = Field(
        default=300, description="Message deduplication TTL in seconds (5 minutes)"
    )
    message_processing_delay_seconds: int = Field(
        default=7, description="Delay in seconds to batch consecutive messages"
    )

    # FAQ Cache Configuration
    faq_cache_enabled: bool = Field(
        default=True, description="Enable FAQ response caching"
    )
    faq_cache_ttl_seconds: int = Field(
        default=3600, description="FAQ cache TTL in seconds (1 hour)"
    )
    faq_cache_max_size: int = Field(
        default=100, description="Maximum number of FAQ responses to cache"
    )

    # Business Hours
    business_hours_start: str = Field(
        default="08:30", description="Business hours start time (HH:MM format)"
    )
    business_hours_end: str = Field(
        default="19:00", description="Business hours end time (HH:MM format)"
    )
    business_hours_sat_end: str = Field(
        default="12:00", description="Saturday business hours end time (HH:MM format)"
    )

    # Policies
    min_booking_advance_hours: int = Field(
        default=1, description="Minimum hours in advance for booking"
    )
    harmonization_cancel_hours: int = Field(
        default=4, description="Minimum hours in advance for harmonization cancellation"
    )
    laser_cancel_hours: int = Field(
        default=24, description="Minimum hours in advance for laser cancellation"
    )
    max_reschedule_count: int = Field(
        default=2, description="Maximum number of reschedules allowed per booking"
    )

    # Reminders
    reminder_d1_hours_before: int = Field(
        default=24, description="Hours before appointment to send D-1 reminder"
    )
    reminder_h2_hours_before: int = Field(
        default=2, description="Hours before appointment to send H-2 reminder"
    )

    # ============================================
    # Monitoring and Observability
    # ============================================
    p95_latency_threshold_ms: int = Field(
        default=7000, description="P95 latency threshold in milliseconds"
    )
    error_rate_threshold_percent: float = Field(
        default=2.0, description="Error rate threshold percentage"
    )
    handover_rate_threshold_percent: float = Field(
        default=30.0, description="Handover rate threshold percentage"
    )

    # Alert configuration
    alert_email: Optional[str] = Field(
        default=None, description="Email address for alerts"
    )
    enable_email_alerts: bool = Field(default=False, description="Enable email alerts")

    # Telemetry configuration
    enable_telemetry: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing/metrics instrumentation",
    )
    telemetry_service_name: str = Field(
        default="clinica-luana-multi-agent",
        description="Service name reported to telemetry backends",
    )
    otel_exporter_otlp_endpoint: Optional[str] = Field(
        default=None,
        description="OTLP collector endpoint (e.g., http://collector:4318)",
    )
    otel_exporter_otlp_insecure: bool = Field(
        default=True,
        description="Disable TLS for OTLP exporter (set False for secure collectors)",
    )

    @field_validator("model_provider")
    @classmethod
    def validate_provider_keys(cls, v, info):
        """Validate that required API keys are present for selected provider."""
        # Note: We can't access other fields in field_validator in Pydantic v2
        # This validation will be done in model_validator
        return v

    def model_post_init(self, __context) -> None:
        """Post-initialization validation."""
        # Normalize shorthand env value
        if self.env == "prod":
            self.env = "production"
        # Only validate LLM keys in production to allow tests/dev without full config
        if self.env == "production":
            if self.model_provider == "xai":
                if not self.xai_api_key:
                    raise ValueError(
                        "XAI_API_KEY is required when MODEL_PROVIDER is set to 'xai'"
                    )
            elif self.model_provider == "gemini":
                if not self.gemini_api_key:
                    raise ValueError(
                        "GEMINI_API_KEY is required when MODEL_PROVIDER is set to 'gemini'"
                    )

    @model_validator(mode="after")
    def validate_provider_after(self):
        """Ensure required API keys are present for the selected provider (only in production)."""
        # Only validate in production; dev/test can skip to allow tests without full config
        if self.env == "production":
            if self.model_provider == "xai" and not self.xai_api_key:
                raise ValueError(
                    "XAI_API_KEY is required when MODEL_PROVIDER is set to 'xai'"
                )
            if self.model_provider == "gemini" and not self.gemini_api_key:
                raise ValueError(
                    "GEMINI_API_KEY is required when MODEL_PROVIDER is set to 'gemini'"
                )
        return self

    def get_llm_config(self) -> LLMConfig:
        """
        Get LLM configuration based on selected provider.

        Returns:
            LLMConfig: Type-safe configuration dictionary with provider-specific settings
        """
        if self.model_provider == "xai":
            if not self.xai_api_key:
                raise ValueError(
                    "XAI_API_KEY is required when MODEL_PROVIDER is set to 'xai'"
                )
            model_name = os.getenv("XAI_MODEL") or self.xai_model
            return create_llm_config(
                provider="xai",
                api_key=self.xai_api_key,
                model=model_name,
                base_url=self.xai_base_url,
                timeout=self.response_timeout_seconds,
                temperature=AgentConstants.DEFAULT_TEMPERATURE,
                max_tokens=AgentConstants.DEFAULT_MAX_TOKENS,
            )
        elif self.model_provider == "gemini":
            if not self.gemini_api_key:
                raise ValueError(
                    "GEMINI_API_KEY is required when MODEL_PROVIDER is set to 'gemini'"
                )
            return create_llm_config(
                provider="gemini",
                api_key=self.gemini_api_key,
                model=self.gemini_model,
                timeout=self.response_timeout_seconds,
                temperature=AgentConstants.DEFAULT_TEMPERATURE,
                max_tokens=AgentConstants.DEFAULT_MAX_TOKENS,
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    @property
    def MODEL_PROVIDER(self) -> str:
        """Get model provider in uppercase for backward compatibility."""
        return self.model_provider.upper()

    @property
    def ENV(self) -> str:
        """Get environment in uppercase for backward compatibility."""
        return self.env.upper()

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env == "development"


# Global settings instance
settings = Settings()
