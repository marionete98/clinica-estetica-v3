"""
Compatibilidade retroativa para o agente de FAQ.

O código refatorado mora em `agents.faq.agent` e `agents.faq.factory`.
Este módulo mantém a API antiga baseada em `create_faq_agent`.
"""

from agents.faq.agent import FAQAgent  # noqa: F401
from agents.faq.factory import COMMON_FAQ_QUESTIONS, create_faq_agent  # noqa: F401

__all__ = ["FAQAgent", "create_faq_agent", "COMMON_FAQ_QUESTIONS"]
