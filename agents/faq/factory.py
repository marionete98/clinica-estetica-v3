"""
Fábrica do agente de FAQ com injeção explícita de dependências.
"""

from __future__ import annotations

from typing import List, Optional

from agents.faq.faq_agent import FAQAgent
from agents.faq.faq_cache_manager import RedisFAQCache
from agents.faq.repositories import KnowledgeBaseRepository, TemplateRepository
from config.llm_config import LLMConfig
from services.container import get_kb_cache_service, get_redis_client
from services.memory.redis_kb_memory import RedisKnowledgeMemory

COMMON_FAQ_QUESTIONS: List[str] = [
    "Quanto custa a depilação a laser?",
    "Qual o horário de funcionamento?",
    "Onde fica a clínica?",
    "Vocês fazem harmonização facial?",
    "Qual a política de cancelamento?",
    "Quantas sessões de laser preciso fazer?",
    "Depilação a laser dói?",
    "Quais são as contraindicações do botox?",
    "Posso fazer laser grávida?",
    "Quanto custa harmonização facial?",
    "Vocês trabalham com Mounjaro?",
    "Tem apartamento para pós-operatório?",
    "Quanto custa o apartamento?",
    "Como funciona a criolipólise?",
    "Vocês fazem preenchimento labial?",
]


def create_faq_agent(
    llm_config: LLMConfig,
    *,
    enable_cache: bool = True,
    cache_ttl_seconds: int = 3600,
    cache_max_size: int = 100,
    knowledge_repository: Optional[KnowledgeBaseRepository] = None,
    template_repository: Optional[TemplateRepository] = None,
    cache: Optional[RedisFAQCache] = None,
    knowledge_memory: Optional[RedisKnowledgeMemory] = None,
) -> FAQAgent:
    """
    Constrói o agente de FAQ com dependências injetáveis.
    """
    repository = knowledge_repository or KnowledgeBaseRepository()
    templates = template_repository or TemplateRepository()
    memory = knowledge_memory or RedisKnowledgeMemory(
        cache_service=get_kb_cache_service(),
        redis_client=get_redis_client(),
    )

    active_cache: Optional[RedisFAQCache] = None
    if enable_cache:
        active_cache = cache or RedisFAQCache(
            redis_client=get_redis_client(),
            ttl_seconds=cache_ttl_seconds,
            max_size=cache_max_size,
        )

    return FAQAgent(
        llm_config=llm_config,
        knowledge_repository=repository,
        template_repository=templates,
        cache=active_cache,
        knowledge_memory=memory,
    )


__all__ = ["create_faq_agent", "COMMON_FAQ_QUESTIONS"]
