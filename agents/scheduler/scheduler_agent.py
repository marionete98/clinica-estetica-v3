"""Agente responsável por fluxos de agendamento e remarcação."""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from autogen_core.tools import FunctionTool

from agents.model_client_factory import create_model_client
from agents.scheduler.booking_handler import (
    build_success_payload,
    ensure_scheduling_hint,
    missing_contact_payload,
    unknown_error_payload,
    validation_error_payload,
)
from agents.scheduler.message_parser import parse_run_result
from agents.scheduler.prompts import SCHEDULER_SYSTEM_PROMPT
from config.llm_config import LLMConfig
from models.agent_schemas import SchedulerAction
from tools.reschedule_tools import (
    cancel_booking,
    check_cancellation_policy,
    reschedule_booking,
)
from tools.scheduler_tools import (
    create_booking,
    get_patient_bookings,
    list_available_slots,
)

logger = logging.getLogger(__name__)


class SchedulerAgent:
    def __init__(self, llm_config: LLMConfig) -> None:
        self.llm_config = llm_config
        self.model_client = create_model_client(llm_config)
        self.agent = AssistantAgent(
            name="scheduler",
            description="Agente de agendamento, remarcação e cancelamento.",
            system_message=SCHEDULER_SYSTEM_PROMPT,
            model_client=self.model_client,
            tools=_build_tools(),
        )

    async def process_request(
        self,
        message: str,
        phone: str,
        contact_id: Optional[str] = None,
        contact_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, object]:
        if not contact_id:
            return missing_contact_payload(phone)

        prompt = _build_prompt(
            message=message,
            phone=phone,
            contact_id=contact_id,
            contact_name=contact_name,
            conversation_id=conversation_id,
            context=context or [],
        )

        try:
            parsed = await self._run_agent(prompt)
        except ValueError:
            return validation_error_payload()
        except Exception:
            logger.exception("Erro no Scheduler Agent")
            return unknown_error_payload()

        parsed["response"] = ensure_scheduling_hint(message, parsed["response"] or "")
        return build_success_payload(parsed)

    async def process_scheduling_request(
        self,
        message: str,
        contact_id: Optional[str],
        phone: str,
        contact_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, object]:
        return await self.process_request(
            message=message,
            phone=phone,
            contact_id=contact_id,
            contact_name=contact_name,
            conversation_id=conversation_id,
            context=context,
        )

    async def cleanup(self) -> None:
        if self.model_client and hasattr(self.model_client, "close"):
            await self.model_client.close()

    async def _run_agent(self, prompt: str) -> Dict[str, object]:
        token = CancellationToken()
        try:
            run_result = await self.agent.run(
                task=prompt,
                session_type=SchedulerAction,
                cancellation_token=token,
            )
            return parse_run_result(run_result)
        finally:
            try:
                if not token.is_cancelled():
                    token.cancel()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Erro ao cancelar token do scheduler: %s", exc)


def _build_prompt(
    *,
    message: str,
    phone: str,
    contact_id: str,
    contact_name: Optional[str],
    conversation_id: Optional[str],
    context: List[Dict[str, str]],
) -> str:
    history = "\n".join(
        f"{msg.get('role','unknown')}: {msg.get('content','')}" for msg in context[-5:]
    )
    contact_section = (
        f"**Informações do Paciente:**\n"
        f"- Nome: {contact_name or 'Não informado'}\n"
        f"- Telefone: {phone}\n"
        f"- Contact ID: {contact_id}\n"
        f"- Conversation ID: {conversation_id or 'N/A'}\n"
    )
    return (
        f"{'**Histórico:**\\n' + history if history else ''}\n"
        f"{contact_section}\n"
        f"**Nova Mensagem do Paciente:**\n{message}\n\n"
        "**Tarefa:**\n"
        "1. Identifique a ação desejada (agendar, remarcar, cancelar, consultar)\n"
        "2. Use as ferramentas apropriadas\n"
        "3. Siga o fluxo correto para cada ação\n"
        "4. SEMPRE solicite confirmação explícita antes de criar/modificar agendamentos\n"
        "5. Seja claro sobre políticas e regras\n"
    )


def _build_tools() -> List[FunctionTool]:
    return [
        _create_list_available_slots_tool(),
        _create_create_booking_tool(),
        _create_get_patient_bookings_tool(),
        _create_cancel_booking_tool(),
        _create_reschedule_booking_tool(),
        _create_check_policy_tool(),
    ]


def _create_list_available_slots_tool() -> FunctionTool:
    async def list_available_slots_tool(
        service_id: str,
        date_range: int = 7,
        start_date: Optional[str] = None,
        max_slots: int = 5,
    ) -> str:
        result = await list_available_slots(
            service_id=service_id,
            date_range=date_range,
            start_date=start_date,
            max_slots=max_slots,
        )
        return json.dumps(result)

    return FunctionTool(
        list_available_slots_tool,
        description=(
            "Consulta horários disponíveis respeitando regras do negócio e retorna até 5 opções."
        ),
    )


def _create_create_booking_tool() -> FunctionTool:
    async def create_booking_tool(
        contact_id: str,
        service_id: str,
        start_datetime: str,
        room: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> str:
        result = await create_booking(
            contact_id=contact_id,
            service_id=service_id,
            start_datetime=start_datetime,
            room=room,
            conversation_id=conversation_id,
        )
        return json.dumps(result)

    return FunctionTool(
        create_booking_tool,
        description="Cria um novo agendamento confirmado após aprovação explícita do paciente.",
    )


def _create_get_patient_bookings_tool() -> FunctionTool:
    async def get_patient_bookings_tool(phone: str) -> str:
        result = await get_patient_bookings(phone=phone)
        return json.dumps(result)

    return FunctionTool(
        get_patient_bookings_tool,
        description="Recupera agendamentos existentes para revisar conflitos ou confirmar detalhes.",
    )


def _create_cancel_booking_tool() -> FunctionTool:
    async def cancel_booking_tool(booking_id: str, reason: Optional[str] = None) -> str:
        result = await cancel_booking(booking_id=booking_id, reason=reason)
        return json.dumps(result)

    return FunctionTool(
        cancel_booking_tool,
        description="Cancela um agendamento aplicando a política vigente e sinalizando impactos.",
    )


def _create_reschedule_booking_tool() -> FunctionTool:
    async def reschedule_booking_tool(
        booking_id: str,
        new_start_datetime: str,
    ) -> str:
        result = await reschedule_booking(
            booking_id=booking_id,
            new_start_datetime=new_start_datetime,
        )
        return json.dumps(result)

    return FunctionTool(
        reschedule_booking_tool,
        description="Reagenda um procedimento mantendo o histórico de contagens e limites.",
    )


def _create_check_policy_tool() -> FunctionTool:
    async def check_cancellation_policy_tool(booking_id: str) -> str:
        result = await check_cancellation_policy(booking_id=booking_id)
        return json.dumps(result)

    return FunctionTool(
        check_cancellation_policy_tool,
        description="Consulta regras de cancelamento aplicáveis ao tratamento informado.",
    )


__all__ = ["SchedulerAgent"]
