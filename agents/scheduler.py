"""
Scheduler Agent for Clínica Luana multi-agent scheduling system.
Responsible for managing appointments: booking, rescheduling, and cancellation.

AutoGen 0.4 Implementation:
- Uses AssistantAgent with async/await pattern
- Tools registered via tools=[] parameter
- Supports both xAI Grok and Google Gemini providers
- Proper resource cleanup with cleanup() method

Usage:
    from agents.scheduler import create_scheduler_agent

    llm_config = {
        "provider": "gemini",  # or "xai"
        "model": "gemini-2.5-flash",
        "api_key": settings.gemini_api_key
    }

    scheduler = create_scheduler_agent(llm_config, use_gemini=True)

    # Process scheduling request (async)
    result = await scheduler.process_scheduling_request(
        message="Quero agendar depilação a laser",
        contact_id="uuid",
        phone="+5594991398585",
        context=conversation_history
    )

    # Cleanup when done
    await scheduler.cleanup()

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3
"""

import json
import logging
from typing import Dict, Any, List, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from openai import AsyncOpenAI
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter
from autogen_core import CancellationToken
from autogen_core.models import ModelInfo
from autogen_core.tools import FunctionTool

from semantic_kernel import Kernel
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.connectors.ai.google.google_ai import (
    GoogleAIChatCompletion,
    GoogleAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)

from models.agent_schemas import SchedulerAction

from tools.scheduler_tools import (
    list_available_slots,
    create_booking,
    get_patient_bookings
)
from tools.reschedule_tools import (
    cancel_booking,
    reschedule_booking,
    check_cancellation_policy
)
from utils.response_parser import parse_messages_from_run_result
from utils.error_handlers import (
    ErrorType,
    get_fallback_response,
    ErrorRecoveryStrategy
)

logger = logging.getLogger(__name__)


# Scheduler agent system prompt with business rules
SCHEDULER_SYSTEM_PROMPT = """
You are the **Scheduling Agent** for Luana Carla Dermo Clinic.

**Language & Tone**
- Always communicate with patients in Portuguese (Brazil).
- Be organized, transparent, and empathetic while enforcing business rules firmly.

**Mission**
- Manage bookings, reschedules, and cancellations without violating clinic policies.
- Keep patients fully informed about timings, rooms, and consequences.

**Critical Business Rules**
1. **Business hours:** Mon-Fri 08:30-19:00, Sat 08:30-12:00, Sun closed. Never offer slots outside this window.
2. **Minimum notice:** only schedule with at least 1 hour of lead time.
3. **Technical buffer:** maintain a 10-minute gap between procedures (system handles it; mention when listing slots).
4. **Cancellation policy:**
   - Facial/body harmonization: cancel with 4h notice to avoid no-show.
   - Laser hair removal: cancel with 24h notice to avoid no-show.
   - Other treatments: 4h standard.
   - Outside the window: warn that the session counts as completed and may be charged.
5. **Reschedule limit:** max 2 reschedules per booking. If `reschedule_count` is 2, deny and send to human support.
6. **No-show guidance:** clearly state that late cancellations count as completed sessions.
7. **Explicit confirmation:** before any booking/reschedule/cancel tool call, obtain a clear "sim", "confirmo", or equivalent.
8. **Action markers:** every operational response must start with `[ACTION:TYPE][BOOKING_ID:UUID or NONE]` (e.g., `[ACTION:BOOKING_CREATED][BOOKING_ID:123...]`).

**Available Tools**
- `list_available_slots`
- `create_booking`
- `get_patient_bookings`
- `reschedule_booking`
- `cancel_booking`
- `check_cancellation_policy`

**Flow: New Booking**
1. Identify the procedure and confirm whether the patient is new or returning.
2. Ask for preferred days/time windows before listing options.
3. Use `list_available_slots` (returns max 5 slots); present up to 3-5 options with date, time, duration, and room (if available).
4. Request explicit confirmation of the chosen slot.
5. Call `create_booking`, then respond with `[ACTION:BOOKING_CREATED]` plus summary, policy reminders, and next steps.

**Flow: Reschedule**
1. Fetch current bookings via `get_patient_bookings` and confirm which one to move.
2. Check the reschedule counter; block if already at 2.
3. Run `check_cancellation_policy` and explain any penalties.
4. Provide new options with `list_available_slots` and wait for confirmation.
5. Execute `reschedule_booking`, return `[ACTION:BOOKING_RESCHEDULED]`, share the remaining reschedule count, and recap details.

**Flow: Cancel**
1. Retrieve bookings with `get_patient_bookings` and confirm the target appointment.
2. Validate policy via `check_cancellation_policy` and warn about consequences if late.
3. Ask whether the patient still wants to cancel.
4. After explicit confirmation, call `cancel_booking`, answer with `[ACTION:BOOKING_CANCELLED]`, and mention no-show impact when applicable.

**Communication Tips**
- Use bullet lists or simple tables for schedule summaries.
- Highlight policy impacts when there is any risk (charges, no-show).
- Explain follow-up steps ("Vou acionar o time para confirmar" / "Nossa equipe liga em seguida").
- Offer alternate channels if limits are reached.

**Late Cancellation Sample**
"Politica aplicada: cancelamentos de depilacao a laser precisam de 24h de antecedencia. Como estamos a 12h do horario, o cancelamento conta como no-show e a sessao podera ser cobrada. Voce confirma mesmo assim?"

Be the guardian of the schedule: enforce rules, keep context clear, and always label actions correctly.
"""


class SchedulerAgent:
    """
    Scheduler Agent for managing appointments.

    This agent:
    - Lists available time slots
    - Creates bookings with validation
    - Reschedules appointments
    - Cancels appointments with policy enforcement
    - Requests explicit confirmation before actions

    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3
    """

    def __init__(
        self,
        llm_config: Dict[str, Any],
    ):
        """
        Initialize Scheduler Agent.

        Args:
            llm_config: LLM configuration dictionary
        """
        self.llm_config = llm_config

        self.model_client = self._create_model_client()
        self.agent = self._create_agent()

        logger.info(
            "Scheduler Agent initialized with AutoGen 0.4 configuration (provider: %s)",
            self.llm_config.get("provider"),
        )

    def _create_model_client(self) -> SKChatCompletionAdapter:
        """
        Create model client using Semantic Kernel.
        
        Uses GoogleAIChatCompletion for Gemini and OpenAIChatCompletion
        with AsyncOpenAI (custom base_url) for xAI Grok or OpenAI.
        
        Returns:
            SKChatCompletionAdapter wrapping the appropriate SK connector
        """
        provider = self.llm_config.get("provider", "xai")

        if provider == "gemini":
            # Gemini via Semantic Kernel GoogleAI connector
            sk_client = GoogleAIChatCompletion(
                gemini_model_id=self.llm_config.get("model", "gemini-1.5-flash"),
                api_key=self.llm_config["api_key"],
            )
            prompt_settings = GoogleAIChatPromptExecutionSettings(
                temperature=self.llm_config.get("temperature", 0.7),
                max_output_tokens=self.llm_config.get("max_tokens", 2048),
            )
        elif provider == "xai":
            # Grok via Semantic Kernel OpenAI connector with custom base_url
            async_client = AsyncOpenAI(
                api_key=self.llm_config["api_key"],
                base_url=self.llm_config.get("base_url", "https://api.x.ai/v1"),
            )
            sk_client = OpenAIChatCompletion(
                ai_model_id=self.llm_config.get("model", "grok-2"),
                async_client=async_client,
            )
            prompt_settings = OpenAIChatPromptExecutionSettings(
                temperature=self.llm_config.get("temperature", 0.7),
                max_tokens=self.llm_config.get("max_tokens", 2048),
            )
        elif provider == "openai":
            # OpenAI via OpenAI-compatible SK connector
            async_client = AsyncOpenAI(
                api_key=self.llm_config["api_key"],
                base_url=self.llm_config.get("base_url", "https://api.openai.com/v1"),
            )
            sk_client = OpenAIChatCompletion(
                ai_model_id=self.llm_config.get("model", "gpt-4o-mini"),
                async_client=async_client,
            )
            prompt_settings = OpenAIChatPromptExecutionSettings(
                temperature=self.llm_config.get("temperature", 0.7),
                max_tokens=self.llm_config.get("max_tokens", 2048),
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Define model capabilities
        model_info = ModelInfo(
            vision=provider == "gemini",
            function_calling=True,
            json_output=True,
            family=provider,
        )
        
        # Wrap SK client with SKChatCompletionAdapter for AutoGen
        return SKChatCompletionAdapter(
            sk_client,
            kernel=Kernel(memory=NullMemory()),
            prompt_settings=prompt_settings,
            model_info=model_info,
        )


    def _create_agent(self) -> AssistantAgent:
        """Create the AutoGen 0.4 AssistantAgent with tools."""
        return AssistantAgent(
            name="scheduler",
            description="Appointment scheduling, rescheduling, and cancellation agent",
            system_message=SCHEDULER_SYSTEM_PROMPT,
            model_client=self.model_client,
            tools=self._build_tools(),
        )

    def _build_tools(self) -> List[FunctionTool]:
        """
        Wrap scheduling helpers with FunctionTool to expose argument schemas and usage
        guidance for the LLM when coordinating bookings.
        """
        # Wrap tools to return JSON strings for SK compatibility
        async def list_available_slots_tool(
            procedure_name: str,
            duration_min: int = 60,
            date_range: int = 7,
            start_date: Optional[str] = None,
            max_slots: int = 5  # Limit to 5 slots for better UX
        ) -> str:
            result = await list_available_slots(
                procedure_name=procedure_name,
                duration_min=duration_min,
                date_range=date_range,
                start_date=start_date,
                max_slots=max_slots
            )
            return json.dumps(result)
        
        async def create_booking_tool(
            phone: str,
            service_type: str,
            datetime_str: str,
            contact_name: Optional[str] = None,
            notes: Optional[str] = None
        ) -> str:
            result = await create_booking(
                phone=phone,
                service_type=service_type,
                datetime_str=datetime_str,
                contact_name=contact_name,
                notes=notes
            )
            return json.dumps(result)
        
        async def get_patient_bookings_tool(phone: str) -> str:
            result = await get_patient_bookings(phone=phone)
            return json.dumps(result)
        
        async def cancel_booking_tool(booking_id: str, reason: Optional[str] = None) -> str:
            result = await cancel_booking(booking_id=booking_id, reason=reason)
            return json.dumps(result)
        
        async def reschedule_booking_tool(
            booking_id: str,
            new_datetime_str: str,
            reason: Optional[str] = None
        ) -> str:
            result = await reschedule_booking(
                booking_id=booking_id,
                new_datetime_str=new_datetime_str,
                reason=reason
            )
            return json.dumps(result)
        
        async def check_cancellation_policy_tool(service_type: str) -> str:
            result = await check_cancellation_policy(service_type=service_type)
            return json.dumps(result)
        
        return [
            FunctionTool(
                list_available_slots_tool,
                description=(
                    "Consulta horários disponíveis futuros respeitando regras de negócio "
                    "como horário de funcionamento, antecedência mínima e intervalos. "
                    "Retorna até 5 opções de horários mais próximos para melhor experiência do paciente."
                ),
            ),
            FunctionTool(
                create_booking_tool,
                description=(
                    "Cria um novo agendamento confirmado após obter a aprovação explícita "
                    "do paciente, registrando serviço, contato e horário escolhido."
                ),
            ),
            FunctionTool(
                get_patient_bookings_tool,
                description=(
                    "Recupera os agendamentos existentes de um paciente pelo telefone para "
                    "verificar conflitos ou listar compromissos ativos."
                ),
            ),
            FunctionTool(
                cancel_booking_tool,
                description=(
                    "Cancela um agendamento respeitando a política vigente e sinalizando "
                    "potenciais consequências de acordo com o tipo de tratamento."
                ),
            ),
            FunctionTool(
                reschedule_booking_tool,
                description=(
                    "Reagenda um procedimento existente, mantendo histórico de contagens e "
                    "validando limites de remarcação."
                ),
            ),
            FunctionTool(
                check_cancellation_policy_tool,
                description=(
                    "Consulta regras de cancelamento aplicáveis ao tratamento informado "
                    "para orientar o paciente sobre prazos e penalidades."
                ),
            ),
        ]

    # Removed _parse_response method - now using centralized utils.response_parser

    async def process_scheduling_request(
        self,
        message: str,
        contact_id: str,
        phone: str,
        contact_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a scheduling-related request.

        AutoGen 0.4 Async Pattern:
        This method demonstrates the async/await pattern required by AutoGen 0.4:
        1. Create CancellationToken for request lifecycle management
        2. Wrap message in TextMessage object
        3. Call agent.on_messages() with await
        4. Parse Response object to extract text

        Args:
            message: User message
            contact_id: Contact UUID
            phone: User's phone number
            contact_name: Optional contact name
            conversation_id: Optional conversation ID
            context: Optional conversation history

        Returns:
            Dictionary with response and action taken:
            {
                "response": "Agendamento confirmado...",
                "action": "booking_created" | "booking_cancelled" | "booking_rescheduled" | "slots_listed" | "info_provided",
                "booking_id": "uuid" (if applicable),
                "requires_confirmation": false
            }
        """
        try:
            logger.info(
                f"Scheduler processing: contact_id={contact_id}, "
                f"message='{message[:50]}...'"
            )

            # Build context string
            context_str = ""
            if context:
                context_str = "\n\n**Histórico:**\n"
                for msg in context[-5:]:  # Last 5 messages
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    context_str += f"{role}: {content}\n"

            # Add contact info
            contact_str = f"""
**Informações do Paciente:**
- Nome: {contact_name or 'Não informado'}
- Telefone: {phone}
- Contact ID: {contact_id}
- Conversation ID: {conversation_id or 'N/A'}
"""

            # Prepare prompt
            prompt = f"""
{context_str}{contact_str}

**Nova Mensagem do Paciente:**
{message}

**Tarefa:**
1. Identifique a ação desejada (agendar, remarcar, cancelar, consultar)
2. Use as ferramentas apropriadas
3. Siga o fluxo correto para cada ação
4. SEMPRE solicite confirmação explícita antes de criar/modificar agendamentos
5. Seja claro sobre políticas e regras
"""

            # Get structured response from agent using AutoGen 0.4 high-level API
            cancellation_token = CancellationToken()
            try:
                run_result = await self.agent.run(
                    task=prompt,
                    cancellation_token=cancellation_token,
                )
                action_obj = run_result.messages[-1].content  # Expected SchedulerAction

                # Check if we got structured output or need to parse text
                if not hasattr(action_obj, "action"):
                    # Fallback: parse as text if structured output not available
                    logger.warning("Scheduler did not return structured output, using text parsing")
                    response_text = parse_messages_from_run_result(run_result, "scheduler")
                    
                    # Check if LLM returned raw JSON from tools
                    if response_text.strip().startswith("[{") and "start_datetime" in response_text:
                        logger.warning("LLM returned raw slot JSON, synthesizing natural response...")
                        try:
                            slots = json.loads(response_text)
                            if slots:
                                response_text = f"Olá! 😊 Encontrei {len(slots)} horários disponíveis para depilação a laser:\n\n"
                                for i, slot in enumerate(slots[:5], 1):  # Show max 5 slots
                                    date = slot.get('date', '')
                                    start = slot.get('start_time', '')
                                    response_text += f"📅 Opção {i}: {date} às {start}\n"
                                response_text += "\nQual horário você prefere? Posso confirmar o agendamento para você! 💙"
                            else:
                                response_text = "Desculpe, não encontrei horários disponíveis para essa data. Gostaria de verificar outra data?"
                        except json.JSONDecodeError:
                            pass  # Keep original response if JSON parsing fails
                    
                    # Use default values when structured output unavailable
                    action = "info_provided"
                    requires_confirmation = False
                    booking_id = None
                else:
                    # Structured output available
                    response_text = action_obj.response
                    action = action_obj.action
                    requires_confirmation = bool(action_obj.requires_confirmation)
                    booking_id = getattr(action_obj, "booking_id", None)
            finally:
                try:
                    if "cancellation_token" in locals() and not cancellation_token.is_cancelled():
                        cancellation_token.cancel()
                except Exception as cleanup_error:
                    logger.warning(f"Error cancelling scheduler token: {cleanup_error}")

            result = {
                "response": response_text,
                "action": action,
                "booking_id": booking_id,
                "requires_confirmation": requires_confirmation,
            }

            logger.info(
                f"Scheduler processed: action={action}, "
                f"requires_confirmation={requires_confirmation}"
            )

            return result

        except ValueError as e:
            # Validation or parsing error - categorize as UNCLEAR_REQUEST
            logger.error(f"Validation error in scheduler: {e}", exc_info=True)
            fallback_msg = get_fallback_response(ErrorType.UNCLEAR_REQUEST)
            return {
                "response": fallback_msg,
                "action": "error",
                "booking_id": None,
                "requires_confirmation": False,
                "error_type": ErrorType.UNCLEAR_REQUEST.value
            }
        except Exception as e:
            # Unknown error - categorize and determine recovery action
            logger.error(f"Error in scheduler agent: {e}", exc_info=True)
            error_type = ErrorType.UNKNOWN_ERROR
            fallback_msg = get_fallback_response(error_type)

            # Get recovery action
            recovery_action = ErrorRecoveryStrategy.get_recovery_action(error_type)

            return {
                "response": fallback_msg,
                "action": "error",
                "booking_id": None,
                "requires_confirmation": False,
                "error_type": error_type.value,
                "recovery_action": recovery_action,
                "should_escalate": recovery_action == "escalate_to_human"
            }

    async def process_request(
        self,
        message: str,
        phone: str,
        contact_id: Optional[str] = None,
        contact_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a scheduling request (wrapper for compatibility).

        Args:
            message: User message
            phone: User's phone number
            contact_id: Optional contact ID
            contact_name: Optional contact name
            conversation_id: Optional conversation ID
            context: Optional conversation history

        Returns:
            Dictionary with response and action taken
        """
        # This is a compatibility wrapper for the orchestrator
        # The orchestrator doesn't have contact_id readily available
        return await self.process_scheduling_request(
            message=message,
            contact_id=contact_id,
            phone=phone,
            contact_name=contact_name,
            conversation_id=conversation_id,
            context=context
        )

    async def cleanup(self):
        """
        Cleanup resources.

        AutoGen 0.4 Resource Management:
        Model clients must be explicitly closed to prevent resource leaks.
        This method should be called when the agent is no longer needed,
        typically on application shutdown.
        """
        if self.model_client and hasattr(self.model_client, 'close'):
            try:
                await self.model_client.close()
                logger.info("Scheduler Agent model client closed")
            except Exception as e:
                logger.error(f"Error closing scheduler model client: {e}")


def create_scheduler_agent(
    llm_config: Dict[str, Any],
) -> SchedulerAgent:
    """
    Factory function to create a Scheduler Agent.

    Args:
        llm_config: LLM configuration dictionary
        prefer_grok: Prefer Grok-4-Reasoning for complex scheduling logic
        use_gemini: Use Gemini 2.5 Flash (recommended, default: True)

    Returns:
        SchedulerAgent instance
    """
    return SchedulerAgent(llm_config)
