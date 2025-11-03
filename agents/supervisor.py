"""
Supervisor Agent for Clínica Luana multi-agent scheduling system.
Responsible for intent classification, routing, and loop detection.
Requirements: 1.4, 6.1
"""

import logging
from typing import Any, Dict, List, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter

from agents.model_client_factory import create_model_client
from config.llm_config import LLMConfig
from models.types import SupervisorClassification
from utils.response_parser import parse_messages_from_run_result
from utils.error_handlers import (
    ErrorType,
    get_fallback_response,
    ErrorRecoveryStrategy
)

logger = logging.getLogger(__name__)


# Intent classification prompt with few-shot examples
SUPERVISOR_SYSTEM_PROMPT = """
You are the **Supervisor Agent** for Luana Carla Dermo Clinic.

Linguagem & Tom
- Responda sempre em Português (Brasil), com voz profissional, acolhedora e objetiva.

Missão
- Ler a última mensagem do paciente e o histórico recente.
- Detectar a intenção dominante e escolher o agente correto.
- Evitar loops de roteamento e proteger a experiência do paciente.

Intenções & Agentes Válidos
- intake — primeiro contato, cumprimentos, apresentação
- faq — dúvidas sobre tratamentos, preços, políticas, horários, contraindicações
- scheduler — agendar, remarcar, cancelar
- escalation — transferência para humano, reclamações, casos sensíveis/urgentes

Prioridade de Roteamento
- Sinais de escalonamento > scheduler > faq > intake.

Gatilhos de Escalonamento (obrigatórios)
- Pedido explícito por atendimento humano/especialista.
- Mesmo agente acionado 3 vezes seguidas sem progresso.
- Urgência clínica, reação adversa ou negociação de alto risco.
- Falta de dados ou baixa confiança para prosseguir.

Formato de Resposta
- Retorne APENAS um dos valores, em minúsculas: `intake`, `faq`, `scheduler`, `escalation`.
"""


class SupervisorAgent:
    """
    Supervisor Agent for intent classification and routing.

    This agent analyzes incoming messages and conversation history to:
    - Classify user intent
    - Route to appropriate functional agent
    - Detect conversation loops
    - Trigger escalation when needed

    Requirements: 1.4, 6.1
    """

    def __init__(self, llm_config: LLMConfig):
        """
        Initialize Supervisor Agent.

        Args:
            llm_config: Type-safe LLM configuration
        """
        self.llm_config = llm_config
        self.model_client = create_model_client(llm_config)
        self.agent = self._create_agent()
        self.routing_history: Dict[str, List[str]] = {}

        logger.info("Supervisor Agent initialized with AutoGen 0.4 configuration")

    def _create_agent(self) -> AssistantAgent:
        """Create the AutoGen 0.4 AssistantAgent."""
        return AssistantAgent(
            name="supervisor",
            description="Intent classification and routing agent",
            system_message=SUPERVISOR_SYSTEM_PROMPT,
            model_client=self.model_client,
        )

    # Removed _parse_response method - now using centralized utils.response_parser

    def _detect_loop(self, conversation_id: str, agent_name: str) -> bool:
        """
        Detect if the same agent has been called 3+ times without progress.

        Args:
            conversation_id: Conversation identifier
            agent_name: Name of agent being routed to

        Returns:
            True if loop detected, False otherwise
        """
        if conversation_id not in self.routing_history:
            self.routing_history[conversation_id] = []

        history = self.routing_history[conversation_id]

        # Check last 3 routing decisions
        if len(history) >= 2:
            # If last 2 were the same agent and we're routing to it again
            if history[-1] == agent_name and history[-2] == agent_name:
                logger.warning(
                    f"Loop detected: {agent_name} called 3+ times "
                    f"for conversation {conversation_id}"
                )
                return True

        return False

    def _update_routing_history(self, conversation_id: str, agent_name: str):
        """
        Update routing history for a conversation.

        Args:
            conversation_id: Conversation identifier
            agent_name: Name of agent being routed to
        """
        if conversation_id not in self.routing_history:
            self.routing_history[conversation_id] = []

        self.routing_history[conversation_id].append(agent_name)

        # Keep only last 5 routing decisions to prevent memory growth
        if len(self.routing_history[conversation_id]) > 5:
            self.routing_history[conversation_id] = self.routing_history[conversation_id][-5:]

    async def classify_intent(
        self,
        message: str,
        conversation_id: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> SupervisorClassification:
        """
        Classify user intent and determine routing.

        Args:
            message: User message to classify
            conversation_id: Conversation identifier
            context: Optional conversation history

        Returns:
            SupervisorClassification dictionary with classification result:
            {
                "intent": "schedule",
                "agent": "scheduler",
                "confidence": "high",
                "loop_detected": false,
                "reasoning": "User wants to book an appointment"
            }
        """
        try:
            logger.info(
                f"Classifying intent: conversation_id={conversation_id}, "
                f"message='{message[:50]}...'"
            )

            # Build context string
            context_str = ""
            if context:
                context_str = "\n\n**Histórico da Conversa:**\n"
                for msg in context[-5:]:  # Last 5 messages
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    context_str += f"{role}: {content}\n"

            # Prepare classification prompt
            classification_prompt = f"""
{context_str}

**Nova Mensagem do Usuário:**
{message}

**Tarefa:**
Classifique a intenção e retorne o agente apropriado.
Responda APENAS com o nome do agente: intake, faq, scheduler, ou escalation
"""

            # Get structured classification from LLM using high-level run()
            cancellation_token = CancellationToken()
            run_result = await self.agent.run(
                task=classification_prompt,
                cancellation_token=cancellation_token,
            )

            # Parse response using centralized parser
            response_text = parse_messages_from_run_result(run_result, "supervisor")

            # Check if response is structured model or string
            decision = run_result.messages[-1].content if hasattr(run_result, "messages") and run_result.messages else response_text

            # Extract structured fields with fallbacks
            if hasattr(decision, "agent"):
                agent_name = getattr(decision, "agent", "").lower()
                confidence = getattr(decision, "confidence", "low")
                reasoning = getattr(decision, "reasoning", "")
            else:
                # Fallback to string parsing when structured output not available
                agent_name = response_text.strip().lower()
                confidence = "low"
                reasoning = "Fallback parsing without structured output"

            # Validate agent name against allowed set
            valid_agents = ["intake", "faq", "scheduler", "escalation"]
            if agent_name not in valid_agents:
                logger.warning(
                    f"Invalid agent name '{agent_name}', defaulting to 'faq'"
                )
                agent_name = "faq"

            # Check for loops and escalate if needed
            loop_detected = self._detect_loop(conversation_id, agent_name)
            if loop_detected:
                logger.info(
                    f"Loop detected, escalating conversation {conversation_id}"
                )
                agent_name = "escalation"

            # Update routing history
            self._update_routing_history(conversation_id, agent_name)

            # Map agent to intent (aligned with test expectations)
            intent_map = {
                "intake": "intake",
                "faq": "faq",
                "scheduler": "scheduling",  # schedule/reschedule/cancel normalized
                "escalation": "escalation",
            }
            intent = intent_map.get(agent_name, "unknown")

            result = {
                "intent": intent,
                "agent": agent_name,
                "confidence": confidence,
                "loop_detected": loop_detected,
                "reasoning": reasoning or f"Routed to {agent_name} based on message content",
            }

            logger.info(
                f"Intent classified: conversation_id={conversation_id}, "
                f"intent={intent}, agent={agent_name}, loop={loop_detected}"
            )

            return result

        except ValueError as e:
            # Response parsing error - categorize as UNCLEAR_REQUEST
            logger.error(f"Error parsing supervisor response: {e}", exc_info=True)
            fallback_msg = get_fallback_response(ErrorType.UNCLEAR_REQUEST)
            return {
                "intent": "escalate",
                "agent": "escalation",
                "confidence": "low",
                "loop_detected": False,
                "reasoning": f"Response parsing error: {str(e)}",
                "error_type": ErrorType.UNCLEAR_REQUEST.value,
                "fallback_message": fallback_msg
            }
        except Exception as e:
            # Unknown error - use heuristic fallback classification instead of always escalating
            logger.error(f"Error classifying intent: {e}", exc_info=True)
            error_type = ErrorType.UNKNOWN_ERROR
            fallback_msg = get_fallback_response(error_type)

            # Simple heuristics on raw message when LLM fails
            try:
                raw_msg = (message or "").lower()
                if any(k in raw_msg for k in ["agendar", "remarcar", "cancelar", "horário", "horarios", "agenda", "marcar"]):
                    agent_name = "scheduler"
                elif any(k in raw_msg for k in ["preço", "valor", "quanto custa", "funcionamento", "horário de funcionamento", "onde fica", "política"]):
                    agent_name = "faq"
                else:
                    agent_name = "intake"

                intent_map = {
                    "intake": "intake",
                    "faq": "faq",
                    "scheduler": "scheduling",
                    "escalation": "escalation",
                }
                intent = intent_map.get(agent_name, "unknown")

                return {
                    "intent": intent,
                    "agent": agent_name,
                    "confidence": "low",
                    "loop_detected": False,
                    "reasoning": f"Heuristic fallback after error: {str(e)}",
                    "error_type": error_type.value,
                    "fallback_message": fallback_msg,
                }
            except Exception:
                # Final fallback to escalation if heuristics also fail
                should_escalate = ErrorRecoveryStrategy.should_escalate(
                    error_count=1,
                    error_type=error_type
                )
                return {
                    "intent": "escalation",
                    "agent": "escalation",
                    "confidence": "low",
                    "loop_detected": False,
                    "reasoning": f"Error during classification (no heuristics): {str(e)}",
                    "error_type": error_type.value,
                    "fallback_message": fallback_msg,
                    "should_escalate": should_escalate
                }
        finally:
            if "cancellation_token" in locals():
                try:
                    cancellation_token.cancel()
                except Exception:
                    pass

    def reset_conversation_history(self, conversation_id: str):
        """
        Reset routing history for a conversation.

        Useful when a conversation is resolved or escalated.

        Args:
            conversation_id: Conversation identifier
        """
        if conversation_id in self.routing_history:
            del self.routing_history[conversation_id]
            logger.info(f"Reset routing history for conversation {conversation_id}")

    def get_routing_history(self, conversation_id: str) -> List[str]:
        """
        Get routing history for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            List of agent names in routing order
        """
        return self.routing_history.get(conversation_id, [])

    async def cleanup(self):
        """Cleanup resources."""
        if self.model_client and hasattr(self.model_client, 'close'):
            try:
                await self.model_client.close()
                logger.info("Supervisor Agent model client closed")
            except Exception as e:
                logger.error(f"Error closing supervisor model client: {e}")


def create_supervisor_agent(llm_config: LLMConfig) -> SupervisorAgent:
    """
    Factory function to create a Supervisor Agent.

    Args:
        llm_config: Type-safe LLM configuration

    Returns:
        SupervisorAgent instance
    """
    return SupervisorAgent(llm_config)
