"""
Utilidades compartilhadas entre componentes de orquestração.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from models.repository import get_session_by_conversation_id

logger = logging.getLogger(__name__)


async def automation_paused(conversation_id: str) -> bool:
    try:
        session = await get_session_by_conversation_id(conversation_id)
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Erro ao consultar status de automação conv_id=%s: %s",
            conversation_id,
            exc,
        )
        return False

    if not session:
        return False

    paused = (
        session.get("automation_paused")
        if isinstance(session, dict)
        else getattr(session, "automation_paused", None)
    )
    if paused:
        logger.info("Automação pausada para conv_id=%s", conversation_id)
    return bool(paused)


def build_payload(
    *,
    decision: Any,
    execution: Any,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    payload = dict(
        response=execution.response_text,
        intent=decision.intent,
        agent=decision.agent_name,
        confidence=execution.confidence,
        should_escalate=execution.should_escalate,
        metadata={
            "provider": provider,
            "loop_detected": decision.loop_detected,
            "context_messages_used": execution.context_usage.get(
                decision.agent_name, 0
            ),
            **execution.metadata,
        },
    )
    if decision.agent_name == "scheduler" and execution.booking_id:
        payload["booking_id"] = execution.booking_id
    return payload


async def cleanup_agents(agents: Dict[str, Any]) -> None:
    for name, agent in agents.items():
        if not agent:
            continue
        try:
            if hasattr(agent, "cleanup"):
                await agent.cleanup()  # type: ignore[func-returns-value]
            elif getattr(agent, "model_client", None):
                await agent.model_client.close()  # type: ignore[func-returns-value]
        except Exception as exc:  # noqa: BLE001
                logger.error("Erro ao limpar agente %s: %s", name, exc, exc_info=True)


PAUSED_PAYLOAD = dict(
    response=None,
    intent="paused",
    agent=None,
    confidence="high",
    should_escalate=False,
    metadata={
        "automation_paused": True,
        "message": "Conversation assigned to human agent",
    },
)


FACTORY_METHODS = {
    "supervisor": "create_supervisor",
    "intake": "create_intake",
    "faq": "create_faq",
    "scheduler": "create_scheduler",
    "escalation": "create_escalation",
}


__all__ = [
    "FACTORY_METHODS",
    "PAUSED_PAYLOAD",
    "automation_paused",
    "build_payload",
    "cleanup_agents",
]
