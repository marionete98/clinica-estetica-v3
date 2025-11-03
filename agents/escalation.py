"""Escalation Agent responsável por preparar handoffs para atendimento humano."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken

from agents.model_client_factory import create_model_client
from config.llm_config import LLMConfig
from utils.error_handlers import (
    ErrorRecoveryStrategy,
    ErrorType,
    get_fallback_response,
)
from utils.response_parser import parse_messages_from_run_result

logger = logging.getLogger(__name__)

ESCALATION_SYSTEM_PROMPT = """
Você é o **Agente de Escalação** da Clínica Luana Carla Dermo.

Missão
- Decidir quando a automação deve ser pausada.
- Preparar o handoff com todas as informações necessárias.

Ao escalar:
1. Valide o sentimento do paciente.
2. Resuma o histórico recente de forma estruturada.
3. Informe o paciente sobre o contato humano e agradeça a paciência.
4. Retorne `ESCALATION_COMPLETE` ao finalizar.
"""


class EscalationAgent:
    def __init__(self, llm_config: LLMConfig) -> None:
        self.llm_config = llm_config
        self.model_client = create_model_client(llm_config)
        self.agent = AssistantAgent(
            name="escalation",
            description="Prepara transferências para atendimento humano.",
            system_message=ESCALATION_SYSTEM_PROMPT,
            model_client=self.model_client,
        )

    async def prepare_escalation(
        self,
        reason: str,
        conversation_id: str,
        contact_info: Dict[str, Any],
        context: Optional[List[Dict[str, str]]] = None,
        intents: Optional[List[str]] = None,
        actions_attempted: Optional[List[str]] = None,
        priority: str = "medium",
    ) -> Dict[str, Any]:
        try:
            summary = self._build_summary(
                reason=reason,
                conversation_id=conversation_id,
                contact_info=contact_info,
                context=context or [],
                intents=intents or [],
                actions=actions_attempted or [],
                priority=priority,
            )
            patient_message = await self._generate_patient_message(
                reason=reason, priority=priority
            )
            return self._build_success_payload(
                summary=summary,
                patient_message=patient_message,
                conversation_id=conversation_id,
                contact_info=contact_info,
                priority=priority,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Error preparing escalation: %s", exc, exc_info=True)
            return self._fallback_payload(exc, contact_info, conversation_id)

    async def detect_escalation_trigger(
        self,
        message: str,
        routing_history: List[str],
        confidence: str = "high",
    ) -> Dict[str, bool]:
        explicit_request = _contains_any(
            message.lower(),
            [
                "falar com alguem",
                "falar com atendente",
                "falar com humano",
                "quero falar",
                "preciso falar",
                "atendente",
                "pessoa",
                "não está resolvendo",
                "não resolve",
                "não ajuda",
            ],
        )
        loop_detected = (
            len(routing_history) >= 3 and len(set(routing_history[-3:])) == 1
        )
        low_confidence = confidence == "low"

        should_escalate = explicit_request or loop_detected or low_confidence
        if explicit_request:
            reason = "Paciente solicitou atendimento humano"
            priority = "medium"
        elif loop_detected:
            reason = "Loop detectado - mesmo agente chamado 3 vezes"
            priority = "high"
        elif low_confidence:
            reason = "Resposta com baixa confiança"
            priority = "medium"
        else:
            reason = "Nenhum gatilho detectado"
            priority = "low"

        return {
            "should_escalate": should_escalate,
            "reason": reason,
            "priority": priority,
        }

    async def cleanup(self) -> None:
        if self.model_client and hasattr(self.model_client, "close"):
            await self.model_client.close()

    # Helpers -----------------------------------------------------------------

    def _build_summary(
        self,
        *,
        reason: str,
        conversation_id: str,
        contact_info: Dict[str, Any],
        context: List[Dict[str, str]],
        intents: List[str],
        actions: List[str],
        priority: str,
    ) -> str:
        history = self._format_conversation_history(context)
        intents_str = ", ".join(intents) if intents else "Nenhuma intenção registrada"
        actions_str = "\n".join(f"- {action}" for action in actions) or "Nenhuma ação registrada"
        return (
            "RESUMO DE ESCALAÇÃO\n"
            "===================\n\n"
            f"Paciente: {contact_info.get('name', 'Não informado')} | "
            f"Telefone: {contact_info.get('phone', 'Não informado')} | "
            f"Email: {contact_info.get('email', 'Não informado')} | "
            f"Contact ID: {contact_info.get('id', 'N/A')}\n\n"
            f"Motivo da Escalação: {reason}\n"
            f"Conversation ID: {conversation_id}\n\n"
            "Histórico recente:\n"
            f"{history}\n\n"
            f"Intenções identificadas: {intents_str}\n"
            f"Ações tentadas:\n{actions_str}\n\n"
            f"Prioridade: {self._priority_label(priority)}\n"
            f"Data/Hora: {datetime.now():%d/%m/%Y %H:%M:%S}\n"
        )

    async def _generate_patient_message(self, *, reason: str, priority: str) -> str:
        prompt = (
            "**Situação:**\n"
            "Precisamos escalar esta conversa para atendimento humano.\n\n"
            f"**Motivo:** {reason}\n"
            f"**Prioridade:** {self._priority_label(priority)}\n\n"
            "**Tarefa:**\n"
            "Escreva uma mensagem curta (2-3 frases), empática e positiva. "
            "Agradeça pela paciência, explique que um especialista continuará o atendimento "
            "em breve e use até dois emojis apropriados. Retorne apenas a mensagem.\n"
        )

        token = CancellationToken()
        try:
            run_result = await self.agent.run(task=prompt, cancellation_token=token)
            text = parse_messages_from_run_result(run_result, "escalation")
        finally:
            try:
                if not token.is_cancelled():
                    token.cancel()
            except Exception as cleanup_error:  # noqa: BLE001
                logger.warning("Error cancelling escalation token: %s", cleanup_error)

        cleaned = text.replace("ESCALATION_COMPLETE", "").strip()
        if "ESCALATION_COMPLETE" not in text:
            cleaned = cleaned.rstrip() + "\n\nESCALATION_COMPLETE"
        return cleaned.replace("ESCALATION_COMPLETE", "").strip()

    def _build_success_payload(
        self,
        *,
        summary: str,
        patient_message: str,
        conversation_id: str,
        contact_info: Dict[str, Any],
        priority: str,
    ) -> Dict[str, Any]:
        return {
            "summary": summary,
            "patient_message": patient_message,
            "conversation_id": conversation_id,
            "priority": priority,
            "should_pause_automation": True,
            "contact_info": contact_info,
            "timestamp": datetime.now().isoformat(),
        }

    def _fallback_payload(
        self,
        exc: Exception,
        contact_info: Dict[str, Any],
        conversation_id: str,
    ) -> Dict[str, Any]:
        error_type = ErrorType.SERVICE_UNAVAILABLE
        fallback_msg = get_fallback_response(error_type)
        return {
            "summary": f"Escalação automática - erro ao gerar resumo: {exc}",
            "patient_message": fallback_msg,
            "conversation_id": conversation_id,
            "priority": "high",
            "should_pause_automation": True,
            "contact_info": contact_info,
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type.value,
            "error_message": str(exc),
        }

    def _priority_label(self, priority: str) -> str:
        mapping = {"low": "Baixa", "medium": "Média", "high": "Alta"}
        return mapping.get(priority.lower(), "Média")

    def _format_conversation_history(
        self, context: List[Dict[str, str]], max_messages: int = 10
    ) -> str:
        if not context:
            return "Nenhum histórico disponível"
        recent = context[-max_messages:]
        lines = []
        for msg in recent:
            role = msg.get("role", "unknown")
            label = {"user": "Paciente", "assistant": "Sistema", "system": "Sistema"}.get(
                role, role.capitalize()
            )
            timestamp = msg.get("timestamp", "")
            content = msg.get("content", "")
            lines.append(f"[{timestamp}] {label}: {content}")
        return "\n".join(lines)


def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def create_escalation_agent(llm_config: LLMConfig) -> EscalationAgent:
    return EscalationAgent(llm_config)


__all__ = ["EscalationAgent", "create_escalation_agent"]
