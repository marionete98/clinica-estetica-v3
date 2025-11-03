"""Factory helpers for constructing agent instances with shared dependencies."""

from __future__ import annotations

import logging
from typing import Optional

from config.llm_config import AgentConstants, LLMConfig, create_llm_config
from config.settings import settings

from agents.escalation import EscalationAgent, create_escalation_agent
from agents.faq import FAQAgent, create_faq_agent
from agents.followup import FollowupAgent, create_followup_agent
from agents.intake import IntakeAgent, create_intake_agent
from agents.scheduler import SchedulerAgent, create_scheduler_agent
from agents.supervisor import SupervisorAgent, create_supervisor_agent

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Central factory for constructing AutoGen agents.

    The factory encapsulates provider-specific configuration tweaks so that
    callers can consistently obtain fully configured agents without duplicating
    setup logic across orchestrators, jobs, or tests.
    """

    def __init__(self, default_llm_config: Optional[LLMConfig] = None):
        self._settings = settings
        self._default_llm_config: LLMConfig = (
            default_llm_config or self._settings.get_llm_config()
        )

    @property
    def default_llm_config(self) -> LLMConfig:
        """Return a defensive copy of the base LLM configuration."""
        return self._default_llm_config.copy()

    def _get_faq_llm_config(self) -> LLMConfig:
        """
        Prefer xAI Grok for FAQ agent when credentials are available to improve
        reasoning over long-form knowledge base content.
        """
        if not self._settings.xai_api_key:
            logger.debug("FAQ agent falling back to default LLM configuration")
            return self.default_llm_config

        return create_llm_config(
            provider="xai",
            model=self._settings.xai_model,
            api_key=self._settings.xai_api_key,
            temperature=AgentConstants.DEFAULT_TEMPERATURE,
            timeout=self._settings.response_timeout_seconds,
            base_url=self._settings.xai_base_url,
        )

    def _get_scheduler_llm_config(self) -> LLMConfig:
        """
        Prefer xAI Grok for scheduler agent for deterministic tool orchestration.
        """
        if not self._settings.xai_api_key:
            logger.debug("Scheduler agent falling back to default LLM configuration")
            return self.default_llm_config

        return create_llm_config(
            provider="xai",
            model=self._settings.xai_model,
            api_key=self._settings.xai_api_key,
            temperature=AgentConstants.DEFAULT_TEMPERATURE,
            timeout=self._settings.response_timeout_seconds,
            base_url=self._settings.xai_base_url,
        )

    def create_supervisor(self, llm_config: Optional[LLMConfig] = None) -> SupervisorAgent:
        """Instantiate Supervisor agent."""
        config = llm_config or self.default_llm_config
        return create_supervisor_agent(config)

    def create_intake(self, llm_config: Optional[LLMConfig] = None) -> IntakeAgent:
        """Instantiate Intake agent."""
        config = llm_config or self.default_llm_config
        return create_intake_agent(config)

    def create_faq(self, llm_config: Optional[LLMConfig] = None) -> FAQAgent:
        """Instantiate FAQ agent with provider-specific configuration."""
        config = llm_config or self._get_faq_llm_config()
        return create_faq_agent(config)

    def create_scheduler(self, llm_config: Optional[LLMConfig] = None) -> SchedulerAgent:
        """Instantiate Scheduler agent with provider-specific configuration."""
        config = llm_config or self._get_scheduler_llm_config()
        return create_scheduler_agent(config)

    def create_escalation(self, llm_config: Optional[LLMConfig] = None) -> EscalationAgent:
        """Instantiate Escalation agent."""
        config = llm_config or self.default_llm_config
        return create_escalation_agent(config)

    def create_followup(self, llm_config: Optional[LLMConfig] = None) -> FollowupAgent:
        """Instantiate Follow-up agent for post-appointment workflows."""
        config = llm_config or self.default_llm_config
        return create_followup_agent(config)


def get_agent_factory(default_llm_config: Optional[LLMConfig] = None) -> AgentFactory:
    """Convenience helper for FastAPI dependency injection."""
    return AgentFactory(default_llm_config=default_llm_config)


__all__ = ["AgentFactory", "get_agent_factory"]
