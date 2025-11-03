"""
Compatibilidade retroativa para o módulo de orquestração.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import Optional

from agents.agent_factory import AgentFactory, get_agent_factory
from config.redis_client import RedisClient
from config.supabase_client import SupabaseOperations
from services.container import get_redis_client, get_supabase_ops
from services.orchestration.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


async def create_orchestrator(
    agent_factory: Optional[AgentFactory] = None,
    redis_client: Optional[RedisClient] = None,
    supabase_ops: Optional[SupabaseOperations] = None,
) -> AgentOrchestrator:
    return AgentOrchestrator(
        agent_factory=agent_factory or get_agent_factory(),
        redis_client=redis_client or get_redis_client(),
        supabase_ops=supabase_ops or get_supabase_ops(),
    )


@asynccontextmanager
async def orchestrator_lifespan():
    orchestrator = AgentOrchestrator(
        agent_factory=get_agent_factory(),
        redis_client=get_redis_client(),
        supabase_ops=get_supabase_ops(),
    )
    try:
        yield orchestrator
    finally:
        await orchestrator.cleanup()


def get_orchestrator() -> AgentOrchestrator:
    logger.warning(
        "get_orchestrator() está depreciado. Use create_orchestrator() com Depends."
    )
    return AgentOrchestrator(
        agent_factory=get_agent_factory(),
        redis_client=get_redis_client(),
        supabase_ops=get_supabase_ops(),
    )


async def orchestrate_agents(
    conversation_id: str, phone: str, message: str
) -> dict:
    orchestrator = AgentOrchestrator(
        agent_factory=get_agent_factory(),
        redis_client=get_redis_client(),
        supabase_ops=get_supabase_ops(),
    )
    try:
        return await orchestrator.orchestrate(conversation_id, phone, message)
    finally:
        await orchestrator.cleanup()


async def cleanup_orchestrator() -> None:
    logger.info(
        "cleanup_orchestrator() chamado. Com DI não há instância global ativa."
    )


__all__ = [
    "AgentOrchestrator",
    "create_orchestrator",
    "orchestrator_lifespan",
    "get_orchestrator",
    "orchestrate_agents",
    "cleanup_orchestrator",
]
