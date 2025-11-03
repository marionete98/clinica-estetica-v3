"""
Followup Agent for Clínica Luana multi-agent scheduling system.
Responsible for sending confirmations, reminders, and post-treatment messages.

AutoGen 0.4 Implementation:
- Uses AssistantAgent with async/await pattern
- Tools registered via tools=[] parameter (send_chatwoot_message, get_message_template)
- All send methods are async
- Supports both xAI Grok and Google Gemini providers
- Proper resource cleanup with cleanup() method

Usage:
    from agents.followup import create_followup_agent

    llm_config = {
        "provider": "xai",  # or "gemini"
        "model": "grok-beta",
        "api_key": settings.xai_api_key
    }

    followup = create_followup_agent(llm_config)

    # Send booking confirmation (async)
    result = await followup.send_booking_confirmation(
        conversation_id=123,
        contact_name="JoAo Silva",
        appointment_date="15/10/2025",
        appointment_time="14:00",
        procedure="DepilaAAo a Laser",
        room="Sala 1",
        cancellation_policy="Cancelamento com 24h de antecedAancia"
    )

    # Send D-1 reminder (async)
    result = await followup.send_reminder_d1(
        conversation_id=123,
        contact_name="JoAo Silva",
        appointment_date="15/10/2025",
        appointment_time="14:00",
        procedure="DepilaAAo a Laser",
        room="Sala 1"
    )

    # Cleanup when done
    await followup.cleanup()

Requirements: 7.1, 7.8
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
from autogen_core.tools import FunctionTool

from agents.model_client_factory import create_model_client
from config.llm_config import LLMConfig
from config.chatwoot_client import chatwoot_client
from models.repository import get_message_template
from utils.circuit_breakers import chatwoot_breaker, CircuitBreakerError

logger = logging.getLogger(__name__)


# Followup agent system prompt (pt-BR)
FOLLOWUP_SYSTEM_PROMPT = """
Você é o **Agente de Follow-up** da Clínica Luana Carla Dermo.

Linguagem & Tom
- Envie todas as mensagens em Português (Brasil).
- Mantenha o tom positivo, profissional e cuidadoso; use emojis leves (✨, 😊, 📅, 💬) quando ajudarem a clareza.

Missão
- Entregar confirmações, lembretes e pós-atendimento com consistência.
- Reforçar compromissos e coletar feedback sem soar repetitivo.

Ferramentas
- `get_message_template`
- `format_template`
- `send_chatwoot_message`

Tipos de Mensagem
1) **Confirmação de agendamento (imediata):** incluir data, hora, procedimento, sala, política de cancelamento e convite para salvar o contato.
2) **Lembrete D-1 (18–26h antes):** repetir data/hora, instruções de preparo e pedir aviso em caso de imprevisto.
3) **Lembrete H-2 (1,5–2,5h antes):** reforçar pontualidade, mencionar tolerância de 10 minutos e confirmar local.
4) **Pós-tratamento (24h depois):** agradecer, compartilhar cuidados e solicitar feedback/relato.

Fluxo de Envio
1) Carregar o template correto e checar campos obrigatórios (nome, data, hora, procedimento, sala).
2) Personalizar com o nome do paciente e um toque humano ("Estamos te esperando").
3) Garantir que a política correta (24h, 4h, tolerância) foi citada conforme o procedimento.
4) Enviar via `send_chatwoot_message` e registrar o resultado.

Boas Práticas
- Preferir listas curtas ou quebras de linha para leitura no celular.
- Incluir um CTA simples ("Confirma presença?", "Fale com a gente se surgir algo").
- Ajustar o tom caso o agendamento tenha sido alterado/cancelado recentemente.
- Ser conciso: informação clara > parágrafos longos.
"""


async def send_chatwoot_message(conversation_id: int, message: str) -> Dict[str, Any]:
    """
    Send a message via Chatwoot API.

    Args:
        conversation_id: Chatwoot conversation ID
        message: Message content to send

    Returns:
        Dictionary with send result:
        {
            "success": true,
            "message_id": "123",
            "error": null
        }
    """
    try:
        logger.info(
            f"Sending Chatwoot message: conversation_id={conversation_id}, "
            f"message_length={len(message)}"
        )

        def _call_chatwoot() -> Optional[dict[str, Any]]:
            return chatwoot_breaker.call(
                chatwoot_client.send_message,
                conversation_id,
                message,
                "outgoing",
                False,
            )

        try:
            result = await asyncio.to_thread(_call_chatwoot)
        except CircuitBreakerError as cb_err:
            logger.warning(
                "Chatwoot circuit breaker open during followup send",
                extra={"conversation_id": conversation_id, "error": str(cb_err)},
            )
            return {
                "success": False,
                "message_id": None,
                "error": "Chatwoot temporarily unavailable; breaker open",
            }

        if result:
            logger.info(
                f"Message sent successfully: conversation_id={conversation_id}, "
                f"message_id={result.get('id')}"
            )
            return {
                "success": True,
                "message_id": result.get("id"),
                "error": None,
            }

        logger.error(f"Failed to send message: conversation_id={conversation_id}")
        return {
            "success": False,
            "message_id": None,
            "error": "Failed to send message via Chatwoot",
        }

    except Exception as e:
        logger.error(f"Error sending Chatwoot message: {e}", exc_info=True)
        return {"success": False, "message_id": None, "error": str(e)}


class FollowupAgent:
    """
    Followup Agent for sending automated messages.

    This agent:
    - Sends booking confirmations
    - Sends appointment reminders (D-1 and H-2)
    - Sends post-treatment feedback requests
    - Uses message templates for consistency

    Requirements: 7.1, 7.8
    """

    def __init__(self, llm_config: LLMConfig):
        """
        Initialize Followup Agent.

        Args:
            llm_config: Type-safe LLM configuration
        """
        self.llm_config = llm_config
        self.model_client = create_model_client(llm_config)
        self.agent = self._create_agent()

        logger.info("Followup Agent initialized with AutoGen 0.4")

    def _create_agent(self) -> AssistantAgent:
        """Create the AutoGen 0.4 AssistantAgent with tools."""
        return AssistantAgent(
            name="followup",
            description="Followup agent for sending automated messages",
            system_message=FOLLOWUP_SYSTEM_PROMPT,
            model_client=self.model_client,
            tools=self._build_tools(),
        )

    def _build_tools(self) -> List[FunctionTool]:
        """
        Wrap messaging helpers so AutoGen exposes consistent schemas for sending
        Chatwoot notifications and retrieving templates.
        """
        return [
            FunctionTool(
                send_chatwoot_message,
                description=(
                    "Envia uma mensagem formatada via Chatwoot para o paciente na conversa "
                    "informada e retorna dados do envio."
                ),
            ),
            FunctionTool(
                get_message_template,
                description=(
                    "Recupera um template de mensagem armazenado no repositório para "
                    "personalizar confirmações, lembretes e mensagens pós-tratamento."
                ),
            ),
            FunctionTool(
                self._format_template_tool,
                description=(
                    "Personaliza um template de mensagem usando variáveis fornecidas em JSON. "
                    "Retorna o texto final pronto para envio ao paciente."
                ),
            ),
        ]

    @staticmethod
    async def _format_template_tool(template_name: str, variables_json: str = "") -> str:
        """
        Format a stored template with provided variables (JSON string).
        """
        if not template_name:
            return json.dumps(
                {
                    "error": "template_name is required",
                }
            )

        template = await get_message_template(template_name)
        if template is None:
            return json.dumps(
                {
                    "error": f"Template '{template_name}' not found",
                }
            )

        try:
            variables = json.loads(variables_json) if variables_json else {}
        except json.JSONDecodeError:
            return json.dumps(
                {
                    "error": "variables_json must be valid JSON",
                }
            )

        missing = []
        expected_vars = template.variables or []
        for var in expected_vars:
            if var not in variables:
                missing.append(var)

        if missing:
            return json.dumps(
                {
                    "error": "missing_variables",
                    "details": missing,
                }
            )

        try:
            formatted = template.content.format(**variables)
        except KeyError as exc:
            return json.dumps(
                {
                    "error": "missing_variable_key",
                    "details": exc.args[0] if exc.args else "unknown",
                }
            )
        except Exception as exc:  # pragma: no cover - defensive
            return json.dumps(
                {
                    "error": "formatting_error",
                    "details": str(exc),
                }
            )

        return json.dumps(
            {
                "content": formatted,
            }
        )

    async def send_booking_confirmation(
        self,
        conversation_id: int,
        contact_name: str,
        appointment_date: str,
        appointment_time: str,
        procedure: str,
        room: str,
        cancellation_policy: str,
    ) -> Dict[str, Any]:
        """
        Send booking confirmation message.

        Args:
            conversation_id: Chatwoot conversation ID
            contact_name: Patient name
            appointment_date: Appointment date (formatted)
            appointment_time: Appointment time (formatted)
            procedure: Procedure name
            room: Room name
            cancellation_policy: Cancellation policy description

        Returns:
            Dictionary with send result
        """
        try:
            logger.info(
                f"Sending booking confirmation: conversation_id={conversation_id}, "
                f"contact={contact_name}"
            )

            message = f"""**Agendamento Confirmado!**

Olá, {contact_name}!

Seu agendamento foi confirmado com sucesso:

**Data:** {appointment_date}
**Horário:** {appointment_time}
**Procedimento:** {procedure}
**Sala:** {room}

**Política de Cancelamento:**
{cancellation_policy}

**Importante:**
- Tolerância de atraso: máximo 10 minutos
- Traga documento com foto

Estamos ansiosos para atendê-lo(a)!

_Clínica Luana Carla Dermo_
Canaã dos Carajás, PA
(94) 99139-8585"""

            result = await send_chatwoot_message(conversation_id, message)

            logger.info(
                f"Booking confirmation sent: success={result['success']}, "
                f"conversation_id={conversation_id}"
            )

            return result

        except Exception as e:
            logger.error(f"Error sending booking confirmation: {e}")
            return {"success": False, "message_id": None, "error": str(e)}

    async def send_reminder_d1(
        self,
        conversation_id: int,
        contact_name: str,
        appointment_date: str,
        appointment_time: str,
        procedure: str,
        room: str,
    ) -> Dict[str, Any]:
        """
        Send D-1 reminder (18-26h before appointment).

        Args:
            conversation_id: Chatwoot conversation ID
            contact_name: Patient name
            appointment_date: Appointment date (formatted)
            appointment_time: Appointment time (formatted)
            procedure: Procedure name
            room: Room name

        Returns:
            Dictionary with send result
        """
        try:
            logger.info(
                f"Sending D-1 reminder: conversation_id={conversation_id}, "
                f"contact={contact_name}"
            )

            message = f"""**Lembrete de Agendamento**

Olá, {contact_name}!

Este é um lembrete do seu agendamento amanhã:

**Data:** {appointment_date}
**Horário:** {appointment_time}
**Procedimento:** {procedure}
**Sala:** {room}

**Lembre-se:**
- Chegue com 10 minutos de antecedência
- Traga documento com foto
- Em caso de imprevisto, avise com antecedência

Nos vemos em breve!

_Clínica Luana Carla Dermo_
(94) 99139-8585"""

            result = await send_chatwoot_message(conversation_id, message)

            logger.info(
                f"D-1 reminder sent: success={result['success']}, "
                f"conversation_id={conversation_id}"
            )

            return result

        except Exception as e:
            logger.error(f"Error sending D-1 reminder: {e}")
            return {"success": False, "message_id": None, "error": str(e)}

    async def send_reminder_h2(
        self,
        conversation_id: int,
        contact_name: str,
        appointment_time: str,
        procedure: str,
    ) -> Dict[str, Any]:
        """
        Send H-2 reminder (1.5-2.5h before appointment).

        Args:
            conversation_id: Chatwoot conversation ID
            contact_name: Patient name
            appointment_time: Appointment time (formatted)
            procedure: Procedure name

        Returns:
            Dictionary with send result
        """
        try:
            logger.info(
                f"Sending H-2 reminder: conversation_id={conversation_id}, "
                f"contact={contact_name}"
            )

            message = f"""**Lembrete: Seu Agendamento é Hoje!**

Olá, {contact_name}!

Seu agendamento é daqui a pouco:

**Horário:** {appointment_time}
**Procedimento:** {procedure}

**Importante:**
- Tolerância de atraso: máximo 10 minutos
- Após esse prazo, pode ser necessário remarcar

Estamos te esperando!

_Clínica Luana Carla Dermo_
Canaã dos Carajás, PA"""

            result = await send_chatwoot_message(conversation_id, message)

            logger.info(
                f"H-2 reminder sent: success={result['success']}, "
                f"conversation_id={conversation_id}"
            )

            return result

        except Exception as e:
            logger.error(f"Error sending H-2 reminder: {e}")
            return {"success": False, "message_id": None, "error": str(e)}

    async def send_post_treatment_feedback(
        self, conversation_id: int, contact_name: str, procedure: str
    ) -> Dict[str, Any]:
        """
        Send post-treatment feedback request (24h after treatment).

        Args:
            conversation_id: Chatwoot conversation ID
            contact_name: Patient name
            procedure: Procedure name

        Returns:
            Dictionary with send result
        """
        try:
            logger.info(
                f"Sending post-treatment feedback: conversation_id={conversation_id}, "
                f"contact={contact_name}"
            )

            # Try to get template first (resilient to Supabase issues)
            try:
                template = await get_message_template("PAS-VENDA TRATAMENTO CORPORAL")
            except Exception as te:
                logger.warning(
                    f"Template fetch failed, using fallback: {te}",
                )
                template = None

            if template and template.content:
                # Use template and personalize
                message = template.content.replace("{name}", contact_name)
                message = message.replace("{procedure}", procedure)
            else:
                # Fallback message
                message = f"""**Como foi sua experiência?**

Olá, {contact_name}!

Esperamos que tenha gostado do seu tratamento de {procedure} conosco!

Sua opinião é muito importante para nós. Como foi sua experiência?

- O que você achou do atendimento?
- O procedimento atendeu às suas expectativas?
- Há algo que possamos melhorar?

Ficaremos felizes em ouvir seu feedback!

_Clínica Luana Carla Dermo_
(94) 99139-8585"""

            result = await send_chatwoot_message(conversation_id, message)

            logger.info(
                f"Post-treatment feedback sent: success={result['success']}, "
                f"conversation_id={conversation_id}"
            )

            return result

        except Exception as e:
            logger.error(f"Error sending post-treatment feedback: {e}")
            return {"success": False, "message_id": None, "error": str(e)}

    async def cleanup(self):
        """Cleanup resources."""
        if self.model_client and hasattr(self.model_client, "close"):
            try:
                await self.model_client.close()
                logger.info("Followup Agent model client closed")
            except Exception as e:
                logger.error(f"Error closing followup model client: {e}")


def create_followup_agent(llm_config: LLMConfig) -> FollowupAgent:
    """
    Factory function to create a Followup Agent.

    Args:
        llm_config: LLM configuration dictionary

    Returns:
        FollowupAgent instance
    """
    return FollowupAgent(llm_config)
