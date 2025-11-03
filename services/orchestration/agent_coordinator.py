"""
Executa os agentes individuais com políticas de retry e parsing auxiliar.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from config.llm_config import AgentConstants
from services.orchestration.conversation_manager import ConversationManager
from services.orchestration.routing_engine import RouteDecision
from utils.circuit_breakers import CircuitBreakerError

logger = logging.getLogger(__name__)

CONTACT_CACHE_PREFIX = "contact:"
CONTACT_CACHE_TTL_SECONDS = 3600
CONTACT_NOT_FOUND_TTL_SECONDS = 300
CONTACT_NOT_FOUND_SENTINEL = {"__not_found__": True}


@dataclass
class AgentExecutionResult:
    response_text: str
    should_escalate: bool
    confidence: str
    metadata: Dict[str, Any]
    context_usage: Dict[str, int]
    booking_id: Optional[str]
    raw_response: Dict[str, Any]


class AgentCoordinator:
    def __init__(self, agent_pool: Any, redis_client: Any, supabase_ops: Any) -> None:
        self._agent_pool = agent_pool
        self._redis = redis_client
        self._supabase_ops = supabase_ops

    async def execute(
        self,
        *,
        decision: RouteDecision,
        conversation_id: str,
        phone: str,
        message: str,
        conversation_manager: ConversationManager,
        default_confidence: str,
    ) -> AgentExecutionResult:
        """
        Executa o agente indicado retornando a resposta normalizada.
        """
        agent = decision.agent_name
        context_usage: Dict[str, int] = {}
        booking_id: Optional[str] = None

        async def _call_agent() -> Dict[str, Any]:
            nonlocal booking_id

            if agent == "intake":
                context = await conversation_manager.load_context(
                    conversation_id, AgentConstants.CONTEXT_WINDOW_INTAKE
                )
                context_usage["intake"] = len(context)
                return await self._agent_pool.intake.process_message(
                    message=message,
                    phone=phone,
                    context=context,
                )

            if agent == "faq":
                context = await conversation_manager.load_context(
                    conversation_id, AgentConstants.CONTEXT_WINDOW_FAQ
                )
                context_usage["faq"] = len(context)
                contact = await self._get_contact(phone)
                contact_name = contact.get("name") if contact else None
                return await self._agent_pool.faq.answer_question(
                    question=message,
                    contact_name=contact_name,
                    context=context,
                )

            if agent == "scheduler":
                context = await conversation_manager.load_context(
                    conversation_id, AgentConstants.CONTEXT_WINDOW_SCHEDULER
                )
                context_usage["scheduler"] = len(context)
                contact = await self._get_contact(phone)
                contact_id = contact.get("id") if contact else None
                contact_name = contact.get("name") if contact else None
                response = await self._agent_pool.scheduler.process_request(
                    message=message,
                    phone=phone,
                    contact_id=contact_id,
                    contact_name=contact_name,
                    conversation_id=conversation_id,
                    context=context,
                )
                parsed = self._parse_scheduler_response(response.get("response", ""))
                response["response"] = parsed["response_text"]
                response["action"] = parsed["action"]
                response["booking_id"] = parsed["booking_id"]
                booking_id = parsed["booking_id"]
                return response

            if agent == "escalation":
                context = await conversation_manager.load_context(
                    conversation_id, AgentConstants.CONTEXT_WINDOW_ESCALATION
                )
                context_usage["escalation"] = len(context)
                contact_info = {
                    "phone": phone,
                    "name": "Não informado",
                    "email": "Não informado",
                    "id": "N/A",
                }
                return await self._agent_pool.escalation.prepare_escalation(
                    reason="loop_detected"
                    if decision.loop_detected
                    else "user_request",
                    conversation_id=conversation_id,
                    contact_info=contact_info,
                    context=context,
                )

            logger.error("Agente desconhecido: %s", agent)
            return {
                "response": (
                    "Desculpe, tive um problema ao processar sua mensagem. "
                    "Vou transferir você para um atendente."
                ),
                "should_escalate": True,
            }

        response: Optional[Dict[str, Any]] = None
        last_error: Optional[Exception] = None

        for attempt in range(2):
            try:
                response = await _call_agent()
                break
            except CircuitBreakerError as cb_err:
                last_error = cb_err
                logger.error(
                    "Circuit breaker aberto ao executar agente %s: %s",
                    agent,
                    cb_err,
                )
                await asyncio.sleep(0.5)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.error(
                    "Erro executando agente %s (tentativa %s): %s",
                    agent,
                    attempt + 1,
                    exc,
                    exc_info=True,
                )
                await asyncio.sleep(0.2)

        if response is None:
            raise RuntimeError(
                f"Falha ao executar agente {agent}"
            ) from last_error

        response_text, should_escalate = self._extract_response(decision, response)
        confidence = response.get("confidence", default_confidence)

        return AgentExecutionResult(
            response_text=response_text,
            should_escalate=should_escalate,
            confidence=confidence,
            metadata=response.get("metadata", {}),
            context_usage=context_usage,
            booking_id=booking_id,
            raw_response=response,
        )

    async def _get_contact(self, phone: str) -> Dict[str, Any]:
        cache_key = f"{CONTACT_CACHE_PREFIX}{phone}"

        try:
            cached = await self._redis.get_value(cache_key, deserialize=True)
            if cached is not None:
                if isinstance(cached, dict) and cached.get("__not_found__"):
                    logger.debug(
                        "Contato não encontrado (cache negativo) telefone=%s", phone
                    )
                    return {}
                logger.debug("Contato encontrado no cache telefone=%s", phone)
                return cached
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Falha ao ler cache de contato telefone=%s: %s", phone, exc
            )

        try:
            contacts = await self._supabase_ops.aselect(
                table="contacts",
                filters={"phone": phone},
                limit=1,
            )
        except CircuitBreakerError as cb_err:
            logger.error(
                "Circuit breaker do Supabase ao buscar contato telefone=%s: %s",
                phone,
                cb_err,
            )
            return {}

        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Erro ao buscar contato telefone=%s: %s", phone, exc
            )
            return {}

        if not contacts:
            await self._redis.set_value(
                cache_key,
                CONTACT_NOT_FOUND_SENTINEL,
                ttl=CONTACT_NOT_FOUND_TTL_SECONDS,
            )
            return {}

        contact = contacts[0]
        try:
            await self._redis.set_value(
                cache_key, contact, ttl=CONTACT_CACHE_TTL_SECONDS
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao salvar contato no cache: %s", exc)

        return contact

    @staticmethod
    def _parse_scheduler_response(raw_response: str) -> Dict[str, Optional[str]]:
        text = raw_response or ""
        action = "info_provided"
        booking_id: Optional[str] = None

        import re

        action_match = re.search(r"\[ACTION:(\w+)\]", text)
        if action_match:
            action = action_match.group(1).lower()
            text = re.sub(r"\[ACTION:\w+\]", "", text)

        booking_match = re.search(r"\[BOOKING_ID:([\w-]+)\]", text)
        if booking_match:
            booking_id = booking_match.group(1)
            text = re.sub(r"\[BOOKING_ID:[\w-]+\]", "", text)

        return {
            "response_text": text.strip(),
            "action": action,
            "booking_id": booking_id,
        }

    @staticmethod
    def _extract_response(
        decision: RouteDecision, response_data: Dict[str, Any]
    ) -> tuple[str, bool]:
        if decision.agent_name == "escalation":
            response_text = response_data.get(
                "patient_message", response_data.get("response", "")
            )
            should_escalate = response_data.get("should_pause_automation", True)
        else:
            response_text = response_data.get(
                "response", response_data.get("answer", "")
            )
            should_escalate = response_data.get("should_escalate", False)
        return response_text, should_escalate


__all__ = ["AgentCoordinator", "AgentExecutionResult"]
