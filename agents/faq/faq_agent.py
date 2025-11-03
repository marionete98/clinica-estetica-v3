from __future__ import annotations
from agents.faq.repositories import KnowledgeBaseRepository, TemplateRepository


import logging
from typing import Any, Dict, List, Optional

from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken

from agents.faq.faq_cache_manager import RedisFAQCache
from agents.faq.prompts import FAQ_SYSTEM_PROMPT
from agents.faq.response_synthesizer import (
    normalize_response,
    strip_low_confidence_marker,
)
from agents.faq.tools import build_tools
from agents.model_client_factory import create_model_client
from config.llm_config import LLMConfig
from services.memory.redis_kb_memory import RedisKnowledgeMemory

from utils.error_handlers import ErrorRecoveryStrategy, ErrorType, get_fallback_response
from utils.response_parser import parse_messages_from_run_result

logger = logging.getLogger(__name__)


class FAQAgent:
    def __init__(
        self,
        llm_config: LLMConfig,
        knowledge_repository: KnowledgeBaseRepository,
        template_repository: TemplateRepository,
        cache: Optional[RedisFAQCache] = None,
        knowledge_memory: Optional[RedisKnowledgeMemory] = None,
    ) -> None:
        self.llm_config = llm_config
        self.kb_repository = knowledge_repository
        self.template_repository = template_repository
        self.cache = cache
        self.memory = knowledge_memory
        self.enable_cache = cache is not None

        self.model_client = create_model_client(llm_config)
        self.agent = AssistantAgent(
            name="faq",
            description="Agente de informações sobre tratamentos, políticas e preços.",
            system_message=FAQ_SYSTEM_PROMPT,
            model_client=self.model_client,
            tools=build_tools(),
            reflect_on_tool_use=True,
        )
    async def answer_question(
        self,
        question: str,
        contact_name: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        try:
            cached = await self._fetchcached_answer(question, contact_name)
            if cached:
                return cached

            prompt = await self._build_prompt(question, contact_name, context)
            raw_text = await self._run_llm(prompt)
            normalized = normalize_response(raw_text)
            response_text, low_confidence = strip_low_confidence_marker(normalized)

            if low_confidence:
                response_text += (
                    "\n\nGostaria de falar com um de nossos especialistas para mais detalhes?"
                )

            result = self._assemble_result(
                response_text=response_text,
                should_escalate=low_confidence,
                offer_booking=self._should_offer_booking(question),
            )

            if not low_confidence:
                await self._store_incache(question, result)

            return result

        except ValueError as err:
            logger.error("Erro interpretando resposta do FAQ: %s", err, exc_info=True)
            fallback = get_fallback_response(ErrorType.UNCLEAR_REQUEST)
            return {
                "answer": fallback,
                "confidence": "low",
                "sources": [],
                "should_escalate": True,
                "offer_booking": False,
                "cached": False,
                "error_type": ErrorType.UNCLEAR_REQUEST.value,
            }

        except Exception as exc:  # noqa: BLE001
            logger.error("Erro no FAQ Agent: %s", exc, exc_info=True)
            err_type = ErrorType.UNKNOWN_ERROR
            recovery = ErrorRecoveryStrategy.get_recovery_action(err_type)
            return {
                "answer": get_fallback_response(err_type),
                "confidence": "low",
                "sources": [],
                "should_escalate": recovery == "escalate_to_human",
                "offer_booking": False,
                "cached": False,
                "error_type": err_type.value,
                "recovery_action": recovery,
            }

    async def _fetchcached_answer(
        self, question: str, contact_name: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        if not self.enable_cache or not self.cache:
            return None
        cached = await self.cache.get(question)
        if not cached:
            return None
        if contact_name and "answer" in cached:
            cached["answer"] = cached["answer"]
        cached["cached"] = True
        return cached

    async def _store_incache(self, question: str, result: Dict[str, Any]) -> None:
        if self.enable_cache and self.cache:
            await self.cache.set(question, result)

    async def _build_prompt(
        self,
        question: str,
        contact_name: Optional[str],
        context: Optional[List[Dict[str, str]]],
    ) -> str:
        parts: List[str] = []
        if context:
            parts.append("**Histórico:**")
            parts.extend(
                f"{msg.get('role','unknown')}: {msg.get('content','')}"
                for msg in context[-3:]
            )
        if contact_name:
            parts.append(f"**Nome do Paciente:** {contact_name}")

        if self.memory:
            hits = await self.memory.query(question, top_k=3)
            if hits:
                lines = []
                for doc in hits[:3]:
                    title = doc.get("title") or doc.get("id", "Documento")
                    excerpt = (doc.get("content") or "").strip()
                    if len(excerpt) > 240:
                        excerpt = excerpt[:237].rsplit(" ", 1)[0] + "..."
                    source = doc.get("source", "memoria")
                    lines.append(f"- **{title}** ({source}): {excerpt}")
                parts.append("**Conhecimento Recuperado:**")
                parts.extend(lines)

        sections = "\n".join(parts)
        return (
            f"{sections}\n\n**Pergunta do Paciente:**\n{question}\n\n"
            "**Tarefa:**\n"
            "1. Busque informações relevantes na base de conhecimento\n"
            "2. Use templates quando apropriado\n"
            "3. Forneça resposta clara e completa\n"
            "4. Mencione contraindicações se relevante\n"
            "5. Ofereça agendamento quando apropriado\n"
            '6. Se não tiver certeza, sinalize com "ESCALATE_LOW_CONFIDENCE"\n'
        )

    async def _run_llm(self, prompt: str) -> str:
        token = CancellationToken()
        try:
            result = await self.agent.run(task=prompt, cancellation_token=token)
            response = parse_messages_from_run_result(result, "faq")
            logger.info("FAQ resposta bruta LLM (500 chars): %s", response[:500])
            return response
        finally:
            try:
                if not token.is_cancelled():
                    token.cancel()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Erro ao cancelar token do FAQ: %s", exc)

    def _assemble_result(
        self, response_text: str, should_escalate: bool, offer_booking: bool
    ) -> Dict[str, Any]:
        confidence = "low" if should_escalate else "high"
        return {
            "answer": response_text,
            "confidence": confidence,
            "sources": [],
            "should_escalate": should_escalate,
            "offer_booking": offer_booking,
            "cached": False,
        }

    def _should_offer_booking(self, question: str) -> bool:
        keywords = {
            "agendar",
            "horário",
            "disponível",
            "marcar",
            "consulta",
            "avaliação",
            "sessão",
        }
        lower_question = question.lower()
        return any(keyword in lower_question for keyword in keywords)

    async def getcache_stats(self) -> Optional[Dict[str, Any]]:
        if not self.enable_cache or not self.cache:
            return None
        return await self.cache.get_stats()

    async def clearcache(self) -> None:
        if self.enable_cache and self.cache:
            await self.cache.clear()

    async def warmcache(self, common_questions: List[str]) -> None:
        if not self.enable_cache or not self.cache:
            logger.warning("Não é possível aquecer o cache: recurso desabilitado")
            return
        for question in common_questions:
            try:
                await self.answer_question(question)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Erro ao aquecer cache para '%s': %s", question[:50], exc
                )

    async def get_treatment_info(self, treatment_name: str) -> Dict[str, Any]:
        try:
            logger.info("Consultando informações do tratamento: %s", treatment_name)
            search_result = await search_knowledge_base(
                query=treatment_name, top_k=1, category="treatments"
            )
            entries = search_result.get("entries", [])
            if not entries:
                return {
                    "found": False,
                    "message": (
                        f"Não encontrei informações sobre '{treatment_name}'. "
                        "Gostaria de falar com nossa equipe?"
                    ),
                }
            treatment = entries[0]
            return {
                "found": True,
                "title": treatment.get("title"),
                "description": treatment.get("content"),
                "category": treatment.get("category"),
                "keywords": treatment.get("keywords", []),
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("Erro ao buscar tratamento '%s': %s", treatment_name, exc)
            return {
                "found": False,
                "message": "Erro ao buscar informações. Por favor, tente novamente.",
            }

    async def cleanup(self) -> None:
        client = getattr(self, "model_client", None)
        if client and hasattr(client, "close"):
            try:
                await client.close()
            except Exception as exc:  # noqa: BLE001
                logger.error("Erro ao fechar cliente do FAQ: %s", exc)


__all__ = ["FAQAgent"]
