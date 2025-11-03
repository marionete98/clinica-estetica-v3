"""
Intake Agent for Clínica Luana multi-agent scheduling system.
Responsável por acolher pacientes, entender necessidades iniciais e encaminhar para o agente adequado sem coletar dados pessoais.
Requirements: 1.2, 1.3
"""

import logging
from typing import Dict, Any, List, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.semantic_kernel import SKChatCompletionAdapter

from agents.model_client_factory import create_model_client
from config.llm_config import LLMConfig
from utils.response_parser import parse_messages_from_run_result
from utils.error_handlers import ErrorType, get_fallback_response, ErrorRecoveryStrategy

logger = logging.getLogger(__name__)


# Intake agent system prompt - optimized with Agent Lightning
INTAKE_SYSTEM_PROMPT = """
You are the **Reception Agent** for Luana Carla Dermo Clinic.

Linguagem & Tom
- Responda em Português (Brasil), de forma acolhedora, humana e concisa.
- Use frases curtas, linguagem simples e profissional. Emojis leves (😊, ✨, 📅) são permitidos quando acrescentam calor humano.

Missão
- Dar boas-vindas, entender a necessidade do paciente e orientar/encaminhar rapidamente para horários e informações.
- Não solicitar dados pessoais (nome, telefone, e-mail) — o telefone do WhatsApp já é conhecido pelo sistema.
- Não realizar cadastro; não salvar/atualizar dados.
- Não solicitar dados sensíveis (CPF, saúde detalhada sem necessidade, documentos). Se necessário, faça handoff para a equipe humana.
- Encerrar com handoff assim que a acolhida estiver concluída (necessidade entendida e próximos passos definidos) e retornar a string final conforme abaixo.

Ferramentas
- Não usar ferramentas de contato (`get_contact_by_phone`, `create_or_update_contact`).
- Nunca pedir o número de telefone ao paciente; utilize o número do WhatsApp implicitamente quando estritamente necessário, sem mencioná-lo.
- Foco: responder dúvidas, oferecer horários e encaminhar ao agendamento (Scheduler).

Fluxo de Conversa
1) Cumprimente calorosamente e pergunte como pode ajudar. Não peça o nome imediatamente após um simples "Olá". Ex.: "Olá! Aqui é da Luana Carla Dermo Clinic — como posso te ajudar hoje? 😊"
2) Não peça telefone. Se necessário, use o número do WhatsApp já disponível no sistema, sem mencioná-lo ao paciente.
3) Evite coletar dados pessoais. Avance direto para atender a solicitação: explicar tratamentos, valores aproximados, orientações e oferecer horários.
4) Não realizar cadastro e não utilizar ferramentas de contato. Quando o paciente quiser prosseguir, encaminhe para o Scheduler para verificar e confirmar horários.
5) Em caso de dúvidas clínicas, explique que fará o repasse para a equipe adequada e realize o handoff.
6) Ofereça ajuda proativa: sugira verificar horários, tipos de procedimento, valores ou orientações pré-consulta. Ex.: "Posso verificar horários disponíveis agora? 📅"
7) Ao concluir a acolhida (necessidade entendida e próximos passos definidos), retorne exatamente a string "INTAKE_COMPLETE".

Boas Práticas
- Prefira parágrafos curtos; mensagens facilmente escaneáveis.
- Use emojis leves quando agregarem calor humano (😊, ✨, 📅), sem exagero.
- Seja proativo: ofereça alternativas e próximos passos claros ("Posso te encaminhar para horários disponíveis?" / "Deseja que eu agende uma avaliação?").
- Em caso de dúvidas técnicas ou necessidade de decisões médicas, explique que você fará o repasse para a equipe adequada e execute o handoff.

Respostas esperadas
- Mensagens acolhedoras, curtas e objetivas que expliquem próximos passos (ex.: verificar horários, tipos de procedimento, valores aproximados).
- Ao final da acolhida, a última saída do agente DEVE ser a string: INTAKE_COMPLETE

Aja agora como Reception Agent seguindo este fluxo.
"""


class IntakeAgent:
    """
    Intake Agent para acolhimento inicial sem coleta de dados.

    Este agente:
    - Recebe pacientes de forma calorosa
    - Identifica necessidades e direciona próximas ações
    - Encaminha para Scheduler ou equipe humana quando apropriado
    - Finaliza acolhidas retornando o marcador INTAKE_COMPLETE

    Requirements: 1.2, 1.3
    """

    def __init__(self, llm_config: LLMConfig):
        """
        Initialize Intake Agent.

        Args:
            llm_config: Type-safe LLM configuration
        """
        self.llm_config = llm_config
        self.model_client = create_model_client(llm_config)
        self.agent = self._create_agent()

        logger.info("Intake Agent initialized with AutoGen 0.4 configuration")

    def _create_agent(self) -> AssistantAgent:
        """Create the AutoGen 0.4 AssistantAgent with tools."""
        return AssistantAgent(
            name="intake",
            description="Patient reception agent focused on guidance and routing without data capture",
            system_message=INTAKE_SYSTEM_PROMPT,
            model_client=self.model_client,
            tools=[],
            reflect_on_tool_use=True,  # Force agent to reflect after tool calls
        )

    async def process_message(
        self, message: str, phone: str, context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a message and guide the patient without collecting new personal data.

        Args:
            message: User message
            phone: User's phone number from WhatsApp
            context: Optional conversation history

        Returns:
            Dictionary with response and status:
            {
                "response": "Bom dia! Seja muito bem-vindo(a)...",
                "status": "collecting" | "complete",
                "contact_id": "uuid" (if complete),
                "contact_info": {...} (if complete)
            }
        """
        try:
            logger.info(
                f"Intake processing message: phone={phone}, message='{message[:50]}...'"
            )

            # Build context string
            context_str = ""
            if context:
                context_str = "\n\n**Histórico:**\n"
                for msg in context[-3:]:  # Last 3 messages
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    context_str += f"{role}: {content}\n"

            # Prepare prompt
            prompt = f"""
{context_str}

**Nova Mensagem do Paciente:**
{message}

**Tarefa:**
1. Cumprimente de forma calorosa e identifique a necessidade principal.
2. Forneça orientações iniciais ou esclareça dúvidas rápidas sem solicitar dados pessoais.
3. Quando o paciente desejar horário ou suporte adicional, encaminhe para o Scheduler ou equipe humana.
4. Encerrada a acolhida (próximos passos definidos), retorne "INTAKE_COMPLETE".
"""

            # Execute via AutoGen 0.4 run() API with cancellation support
            cancellation_token = CancellationToken()
            run_result = await self.agent.run(
                task=prompt,
                cancellation_token=cancellation_token,
            )
            try:
                response_text = parse_messages_from_run_result(run_result, "intake").strip()
            except ValueError as parse_error:
                logger.error(
                    f"Failed to parse intake response: {parse_error}", exc_info=True
                )
                response_text = get_fallback_response(
                    ErrorType.PARSING, ErrorRecoveryStrategy.RETRY
                )
                is_complete = False
            else:
                logger.debug(
                    f"Intake agent response extracted: {response_text[:100]}..."
                )
                is_complete = "INTAKE_COMPLETE" in response_text
                if is_complete:
                    response_text = response_text.replace("INTAKE_COMPLETE", "").strip()

            # Remove the completion marker from response
            if is_complete:
                response_text = response_text.replace("INTAKE_COMPLETE", "").strip()

            result = {
                "response": response_text,
                "status": "complete" if is_complete else "collecting",
                "contact_id": None,
                "contact_info": None,
            }

            logger.info(
                f"Intake processed: phone={phone}, status={result['status']}, "
                "contact handling skipped by policy"
            )

            return result

        except ValueError as e:
            # Validation error (e.g., invalid phone) - categorize as UNCLEAR_REQUEST
            logger.error(f"Validation error in intake: {e}", exc_info=True)
            fallback_msg = get_fallback_response(ErrorType.UNCLEAR_REQUEST)
            return {
                "response": fallback_msg,
                "status": "error",
                "contact_id": None,
                "contact_info": None,
                "error_type": ErrorType.UNCLEAR_REQUEST.value,
            }
        except Exception as e:
            # Unknown error - categorize and determine recovery action
            logger.error(f"Error in intake agent: {e}", exc_info=True)
            error_type = ErrorType.UNKNOWN_ERROR
            fallback_msg = get_fallback_response(error_type)

            # Get recovery action
            recovery_action = ErrorRecoveryStrategy.get_recovery_action(error_type)

            return {
                "response": fallback_msg,
                "status": "error",
                "contact_id": None,
                "contact_info": None,
                "error_type": error_type.value,
                "recovery_action": recovery_action,
                "should_escalate": recovery_action == "escalate_to_human",
            }
        finally:
            if "cancellation_token" in locals():
                try:
                    cancellation_token.cancel()
                except Exception:
                    pass
    async def quick_register(
        self, phone: str, name: str, email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Legacy helper mantido por compatibilidade. Novas políticas impedem cadastro automático.
        """
        logger.warning("Quick register attempted but disabled by contact data policy")
        return {
            "success": False,
            "contact_id": None,
            "contact_info": None,
            "message": (
                "Cadastro automático indisponível. A equipe humana deve registrar os dados conforme necessário."
            ),
        }

    async def cleanup(self):
        """Cleanup resources."""
        if self.model_client and hasattr(self.model_client, "close"):
            try:
                await self.model_client.close()
                logger.info("Intake Agent model client closed")
            except Exception as e:
                logger.error(f"Error closing intake model client: {e}")


def create_intake_agent(llm_config: LLMConfig) -> IntakeAgent:
    """
    Factory function to create an Intake Agent.

    Args:
        llm_config: LLM configuration dictionary

    Returns:
        IntakeAgent instance
    """
    return IntakeAgent(llm_config)
