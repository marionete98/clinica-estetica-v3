"""Coordena chamadas aos agentes especializados e normaliza respostas."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

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


@dataclass
class AgentCallResult:
    payload: Dict[str, Any]
    context_key: Optional[str] = None
    context_size: int = 0
    booking_id: Optional[str] = None


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
        agent_name = decision.agent_name
        context_usage: Dict[str, int] = {}

        async def invoke() -> AgentCallResult:
            return await self._invoke_agent(
                agent_name=agent_name,
                decision=decision,
                conversation_id=conversation_id,
                phone=phone,
                message=message,
                conversation_manager=conversation_manager,
            )

        call_result = await self._call_with_retry(agent_name, invoke)
        if call_result.context_key:
            context_usage[call_result.context_key] = call_result.context_size

        payload = call_result.payload
        response_text, should_escalate = self._extract_response(decision, payload)
        confidence = payload.get("confidence", default_confidence)

        metadata_raw = payload.get("metadata") if isinstance(payload, dict) else {}
        metadata = dict(metadata_raw) if isinstance(metadata_raw, dict) else {}
        if agent_name == "scheduler":
            metadata.setdefault("action", payload.get("action"))
            metadata.setdefault(
                "requires_confirmation",
                payload.get("requires_confirmation", False),
            )
        payload["metadata"] = metadata

        return AgentExecutionResult(
            response_text=response_text,
            should_escalate=should_escalate,
            confidence=confidence,
            metadata=metadata,
            context_usage=context_usage,
            booking_id=call_result.booking_id or payload.get("booking_id"),
            raw_response=payload,
        )

    async def _call_with_retry(
        self,
        agent_name: str,
        call: Callable[[], Awaitable[AgentCallResult]],
    ) -> AgentCallResult:
        last_error: Optional[Exception] = None
        for attempt in range(2):
            try:
                return await call()
            except CircuitBreakerError as cb_err:
                last_error = cb_err
                logger.error(
                    "Circuit breaker aberto ao executar agente %s: %s",
                    agent_name,
                    cb_err,
                )
                await asyncio.sleep(0.5)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.error(
                    "Erro executando agente %s (tentativa %s): %s",
                    agent_name,
                    attempt + 1,
                    exc,
                    exc_info=True,
                )
                await asyncio.sleep(0.2)

        raise RuntimeError(f"Falha ao executar agente {agent_name}") from last_error

    async def _invoke_agent(
        self,
        *,
        agent_name: str,
        decision: RouteDecision,
        conversation_id: str,
        phone: str,
        message: str,
        conversation_manager: ConversationManager,
    ) -> AgentCallResult:
        if agent_name == "intake":
            return await self._run_intake(
                conversation_id, phone, message, conversation_manager
            )
        if agent_name == "faq":
            return await self._run_faq(
                conversation_id, phone, message, conversation_manager
            )
        if agent_name == "scheduler":
            return await self._run_scheduler(
                decision,
                conversation_id,
                phone,
                message,
                conversation_manager,
            )
        if agent_name == "escalation":
            return await self._run_escalation(
                decision,
                conversation_id,
                phone,
                message,
                conversation_manager,
            )

        logger.error("Agente desconhecido: %s", agent_name)
        return AgentCallResult(
            payload={
                "response": (
                    "Desculpe, tive um problema ao processar sua mensagem. "
                    "Vou transferir você para um atendente."
                ),
                "should_escalate": True,
            }
        )

    async def _run_intake(
        self,
        conversation_id: str,
        phone: str,
        message: str,
        conversation_manager: ConversationManager,
    ) -> AgentCallResult:
        context = await conversation_manager.load_context(
            conversation_id, AgentConstants.CONTEXT_WINDOW_INTAKE
        )
        payload = await self._agent_pool.intake.process_message(
            message=message,
            phone=phone,
            context=context,
        )
        return AgentCallResult(
            payload=payload,
            context_key="intake",
            context_size=len(context),
        )

    async def _run_faq(
        self,
        conversation_id: str,
        phone: str,
        message: str,
        conversation_manager: ConversationManager,
    ) -> AgentCallResult:
        context = await conversation_manager.load_context(
            conversation_id, AgentConstants.CONTEXT_WINDOW_FAQ
        )
        contact = await self._get_contact(phone)
        contact_name = contact.get("name") if contact else None
        payload = await self._agent_pool.faq.answer_question(
            question=message,
            contact_name=contact_name,
            context=context,
        )
        return AgentCallResult(
            payload=payload,
            context_key="faq",
            context_size=len(context),
        )

    async def _run_scheduler(
        self,
        decision: RouteDecision,
        conversation_id: str,
        phone: str,
        message: str,
        conversation_manager: ConversationManager,
    ) -> AgentCallResult:
        context = await conversation_manager.load_context(
            conversation_id, AgentConstants.CONTEXT_WINDOW_SCHEDULER
        )
        contact = await self._get_contact(phone)
        contact_id = contact.get("id") if contact else None
        contact_name = contact.get("name") if contact else None
        payload = await self._agent_pool.scheduler.process_request(
            message=message,
            phone=phone,
            contact_id=contact_id,
            contact_name=contact_name,
            conversation_id=conversation_id,
            context=context,
        )
        parsed = self._parse_scheduler_response(payload.get("response", ""))
        payload["response"] = parsed["response_text"]
        payload["action"] = parsed["action"]
        payload["booking_id"] = parsed["booking_id"]
        return AgentCallResult(
            payload=payload,
            context_key="scheduler",
            context_size=len(context),
            booking_id=parsed["booking_id"],
        )

    async def _run_escalation(
        self,
        decision: RouteDecision,
        conversation_id: str,
        phone: str,
        message: str,
        conversation_manager: ConversationManager,
    ) -> AgentCallResult:
        context = await conversation_manager.load_context(
            conversation_id, AgentConstants.CONTEXT_WINDOW_ESCALATION
        )
        contact = await self._get_contact(phone)
        contact_info = {
            "phone": phone,
            "name": (
                contact.get("name", "Não informado") if contact else "Não informado"
            ),
            "email": (
                contact.get("email", "Não informado") if contact else "Não informado"
            ),
            "id": contact.get("id", "N/A") if contact else "N/A",
        }
        payload = await self._agent_pool.escalation.prepare_escalation(
            reason="loop_detected" if decision.loop_detected else "user_request",
            conversation_id=conversation_id,
            contact_info=contact_info,
            context=context,
        )
        return AgentCallResult(
            payload=payload,
            context_key="escalation",
            context_size=len(context),
        )

    async def _get_contact(self, phone: str) -> Dict[str, Any]:
        cache_key = f"{CONTACT_CACHE_PREFIX}{phone}"
        cached = await self._read_contact_cache(cache_key, phone)
        if cached is not None:
            return cached

        contact = await self._fetch_contact_from_supabase(phone)
        await self._write_contact_cache(cache_key, contact)
        return contact

    async def _read_contact_cache(
        self, cache_key: str, phone: str
    ) -> Optional[Dict[str, Any]]:
        try:
            cached = await self._redis.get_value(cache_key, deserialize=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao ler cache de contato telefone=%s: %s", phone, exc)
            return None

        if cached is None:
            return None
        if isinstance(cached, dict) and cached.get("__not_found__"):
            logger.debug("Contato não encontrado (cache negativo) telefone=%s", phone)
            return {}
        logger.debug("Contato encontrado no cache telefone=%s", phone)
        return cached

    async def _fetch_contact_from_supabase(self, phone: str) -> Dict[str, Any]:
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
            logger.error("Erro ao buscar contato telefone=%s: %s", phone, exc)
            return {}

        return contacts[0] if contacts else {}

    async def _write_contact_cache(
        self, cache_key: str, contact: Dict[str, Any]
    ) -> None:
        try:
            if contact:
                await self._redis.set_value(
                    cache_key, contact, ttl=CONTACT_CACHE_TTL_SECONDS
                )
            else:
                await self._redis.set_value(
                    cache_key,
                    CONTACT_NOT_FOUND_SENTINEL,
                    ttl=CONTACT_NOT_FOUND_TTL_SECONDS,
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao salvar contato no cache: %s", exc)

    @staticmethod
    def _parse_scheduler_response(raw_response: str) -> Dict[str, Optional[str]]:
        text = raw_response or ""
        action = "info_provided"
        booking_id: Optional[str] = None

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


__all__ = ["AgentCoordinator", "AgentExecutionResult", "AgentCallResult"]
