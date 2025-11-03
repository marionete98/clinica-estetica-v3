"""Define lógica de roteamento entre agentes com base em intenções."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from config.llm_config import AgentConstants
from services.orchestration.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


@dataclass
class RouteDecision:
    intent: str
    agent_name: str
    loop_detected: bool
    supervisor_context: List[Dict[str, str]]
    raw_classification: Dict[str, Any]


class RoutingEngine:
    def __init__(
        self, supervisor_agent: Any, conversation_manager: ConversationManager
    ) -> None:
        self._supervisor = supervisor_agent
        self._conversation_manager = conversation_manager

    async def determine_route(
        self, *, conversation_id: str, message: str
    ) -> RouteDecision:
        """
        Carrega o contexto relevante e delega a classificação ao Supervisor.
        """
        context = await self._conversation_manager.load_context(
            conversation_id, AgentConstants.CONTEXT_WINDOW_SUPERVISOR
        )

        classification = await self._supervisor.classify_intent(
            message=message,
            conversation_id=conversation_id,
            context=context,
        )

        intent = classification["intent"]
        agent_name = classification["agent"]
        loop_detected = classification.get("loop_detected", False)

        logger.info(
            "Intenção classificada: intent=%s agent=%s loop=%s",
            intent,
            agent_name,
            loop_detected,
        )

        return RouteDecision(
            intent=intent,
            agent_name=agent_name,
            loop_detected=loop_detected,
            supervisor_context=context,
            raw_classification=classification,
        )


__all__ = ["RoutingEngine", "RouteDecision"]
