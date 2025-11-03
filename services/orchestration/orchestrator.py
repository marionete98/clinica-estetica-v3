from __future__ import annotations

import logging
from typing import Dict, Optional

from agents.agent_factory import AgentFactory, get_agent_factory
from config.redis_client import RedisClient
from config.supabase_client import SupabaseOperations
from services.container import get_redis_client, get_supabase_ops
from services.orchestration.agent_coordinator import AgentCoordinator
from services.orchestration.conversation_manager import ConversationManager
from services.orchestration.routing_engine import RoutingEngine
from services.orchestration.utils import (
    FACTORY_METHODS,
    PAUSED_PAYLOAD,
    automation_paused,
    build_payload,
    cleanup_agents,
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    def __init__(
        self,
        agent_factory: Optional[AgentFactory] = None,
        redis_client: Optional[RedisClient] = None,
        supabase_ops: Optional[SupabaseOperations] = None,
    ) -> None:
        self.agent_factory = agent_factory or get_agent_factory()
        self.redis_client = redis_client or get_redis_client()
        self.supabase_ops = supabase_ops or get_supabase_ops()

        self.llm_config = self.agent_factory.default_llm_config
        self.agents = {
            name: getattr(self.agent_factory, method)()
            for name, method in FACTORY_METHODS.items()
        }
        self.conversation_manager = ConversationManager(self.redis_client)
        self.routing_engine = RoutingEngine(
            supervisor_agent=self.agents["supervisor"],
            conversation_manager=self.conversation_manager,
        )
        self.agent_coordinator = AgentCoordinator(
            agent_pool=self.agents,
            redis_client=self.redis_client,
            supabase_ops=self.supabase_ops,
        )

    async def orchestrate(
        self, conversation_id: str, phone: str, message: str
    ) -> Dict[str, Any]:
        if await automation_paused(conversation_id):
            return PAUSED_PAYLOAD

        decision = await self.routing_engine.determine_route(
            conversation_id=conversation_id, message=message
        )

        execution = await self.agent_coordinator.execute(
            decision=decision,
            conversation_id=conversation_id,
            phone=phone,
            message=message,
            conversation_manager=self.conversation_manager,
            default_confidence=decision.raw_classification.get(
                "confidence", "medium"
            ),
        )

        if execution.response_text:
            await self.conversation_manager.append_context(
                conversation_id, message, execution.response_text
            )

        return build_payload(
            decision=decision,
            execution=execution,
            provider=self.llm_config.get("provider"),
        )

    async def cleanup(self) -> None:
        await cleanup_agents(self.agents)


__all__ = ["AgentOrchestrator"]
