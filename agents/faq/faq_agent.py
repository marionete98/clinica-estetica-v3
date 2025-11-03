"""Implementação do agente de FAQ com etapas orquestradas."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken

from agents.faq.faq_cache_manager import RedisFAQCache
from agents.faq.prompts import FAQ_SYSTEM_PROMPT
from agents.faq.repositories import KnowledgeBaseRepository, TemplateRepository
from agents.faq.response_synthesizer import (
    normalize_response,
    strip_low_confidence_marker,
)
from agents.faq.tools import build_tools
from agents.model_client_factory import create_model_client
from config.llm_config import LLMConfig
from services.memory.redis_kb_memory import RedisKnowledgeMemory
from tools.kb_tools_cached import search_knowledge_base
from utils.error_handlers import ErrorRecoveryStrategy, ErrorType, get_fallback_response
from utils.response_parser import parse_messages_from_run_result

logger = logging.getLogger(__name__)


TEMPLATE_KEYWORDS: Dict[str, str] = {
    "cancel": "faq_cancellation_policy",
    "cancelamento": "faq_cancellation_policy",
    "horário": "faq_operating_hours",
    "horario": "faq_operating_hours",
    "preço": "faq_pricing",
    "valor": "faq_pricing",
    "custo": "faq_pricing",
    "contraindicação": "faq_contraindications",
    "contraindicacao": "faq_contraindications",
}


@dataclass
class KnowledgeSection:
    title: str
    excerpt: str
    source: str


@dataclass
class TemplateInfo:
    name: str
    content: str


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
            return await self._generate_answer(
                question=question,
                contact_name=contact_name,
                context=context or [],
            )
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

    async def _generate_answer(
        self,
        *,
        question: str,
        contact_name: Optional[str],
        context: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        cached = await self._fetch_cached_answer(question, contact_name)
        if cached:
            return cached

        knowledge_sections = await self._search_kb(question)
        template = await self._find_template(question)
        prompt = await self._build_prompt(
            question=question,
            contact_name=contact_name,
            context=context,
            knowledge_sections=knowledge_sections,
            template=template,
        )
        raw_text = await self._run_llm(prompt)
        response_text, low_confidence = self._synthesize_response(raw_text, template)

        result = self._format_final_response(
            response_text=response_text,
            low_confidence=low_confidence,
            question=question,
            knowledge_sections=knowledge_sections,
        )

        if not low_confidence:
            await self._store_in_cache(question, result)

        return result

    async def _fetch_cached_answer(
        self, question: str, contact_name: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        if not self.enable_cache or not self.cache:
            return None
        cached = await self.cache.get(question)
        if not cached:
            return None
        if contact_name and "answer" in cached:
            cached["answer"] = cached["answer"].replace("{name}", contact_name)
        cached["cached"] = True
        return cached

    async def _store_in_cache(self, question: str, result: Dict[str, Any]) -> None:
        if self.enable_cache and self.cache:
            await self.cache.set(question, result)

    async def _search_kb(self, question: str) -> List[KnowledgeSection]:
        memory_hits = await self._search_memory(question)
        if memory_hits:
            return memory_hits
        return await self._search_repository(question)

    async def _search_memory(self, question: str) -> List[KnowledgeSection]:
        if not self.memory:
            return []
        try:
            documents = await self.memory.query(question, top_k=3)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao consultar memória do FAQ: %s", exc)
            return []
        return [self._to_knowledge_section(doc) for doc in documents[:3]]

    async def _search_repository(self, question: str) -> List[KnowledgeSection]:
        keywords = self._extract_keywords(question)
        if not keywords:
            return []
        try:
            records = await self.kb_repository.search(keywords[:5])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao consultar base de conhecimento: %s", exc)
            return []
        sections: List[KnowledgeSection] = []
        for record in records[:3]:
            title = getattr(record, "title", "Documento")
            content = getattr(record, "content", "")
            sections.append(
                KnowledgeSection(
                    title=title,
                    excerpt=self._trim_excerpt(content),
                    source=getattr(record, "category", "knowledge_base")
                    or "knowledge_base",
                )
            )
        return sections

    async def _find_template(self, question: str) -> Optional[TemplateInfo]:
        lowered = question.lower()
        for keyword, template_name in TEMPLATE_KEYWORDS.items():
            if keyword in lowered:
                try:
                    template = await self.template_repository.get(template_name)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Falha ao recuperar template '%s': %s", template_name, exc
                    )
                    continue
                if template:
                    return TemplateInfo(name=template_name, content=template.content)
        return None

    async def _build_prompt(
        self,
        *,
        question: str,
        contact_name: Optional[str],
        context: Sequence[Dict[str, str]],
        knowledge_sections: Sequence[KnowledgeSection],
        template: Optional[TemplateInfo],
    ) -> str:
        sections: List[str] = []
        history = self._build_context_section(context)
        if history:
            sections.append(history)
        contact_section = self._build_contact_section(contact_name)
        if contact_section:
            sections.append(contact_section)
        knowledge = self._build_knowledge_section(knowledge_sections)
        if knowledge:
            sections.append(knowledge)
        template_section = self._build_template_section(template)
        if template_section:
            sections.append(template_section)

        instructions = (
            "**Tarefa:**\n"
            "1. Use o contexto e conhecimento para responder com precisão.\n"
            "2. Cite contraindicações quando relevante.\n"
            "3. Indique possibilidade de agendamento quando fizer sentido.\n"
            '4. Se não tiver certeza, sinalize com "ESCALATE_LOW_CONFIDENCE".\n'
        )

        sections.append(f"**Pergunta do Paciente:**\n{question.strip()}\n")
        sections.append(instructions)
        return "\n\n".join(section for section in sections if section)

    def _build_context_section(
        self, context: Sequence[Dict[str, str]]
    ) -> Optional[str]:
        if not context:
            return None
        messages = [
            f"{msg.get('role', 'unknown')}: {msg.get('content', '').strip()}"
            for msg in context[-3:]
        ]
        if not messages:
            return None
        return "**Histórico:**\n" + "\n".join(messages)

    def _build_contact_section(self, contact_name: Optional[str]) -> Optional[str]:
        if not contact_name:
            return None
        return f"**Nome do Paciente:** {contact_name}"

    def _build_knowledge_section(
        self, knowledge_sections: Sequence[KnowledgeSection]
    ) -> Optional[str]:
        if not knowledge_sections:
            return None
        lines = ["**Conhecimento Recuperado:**"]
        for section in knowledge_sections:
            lines.append(f"- **{section.title}** ({section.source}): {section.excerpt}")
        return "\n".join(lines)

    def _build_template_section(
        self, template: Optional[TemplateInfo]
    ) -> Optional[str]:
        if not template:
            return None
        return f"**Template Sugerido ({template.name}):**\n{template.content.strip()}"

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

    def _synthesize_response(
        self, raw_text: str, template: Optional[TemplateInfo]
    ) -> tuple[str, bool]:
        normalized = normalize_response(raw_text)
        response_text, low_confidence = strip_low_confidence_marker(normalized)
        if not response_text and template:
            response_text = template.content
        if low_confidence:
            response_text = response_text.rstrip() + (
                "\n\nGostaria de falar com um de nossos especialistas para mais detalhes?"
            )
        return response_text, low_confidence

    def _format_final_response(
        self,
        *,
        response_text: str,
        low_confidence: bool,
        question: str,
        knowledge_sections: Sequence[KnowledgeSection],
    ) -> Dict[str, Any]:
        offer_booking = self._should_offer_booking(question)
        confidence = "low" if low_confidence else "high"
        return {
            "answer": response_text,
            "confidence": confidence,
            "sources": self._format_sources(knowledge_sections),
            "should_escalate": low_confidence,
            "offer_booking": offer_booking,
            "cached": False,
        }

    def _format_sources(
        self, knowledge_sections: Sequence[KnowledgeSection]
    ) -> List[Dict[str, str]]:
        sources: List[Dict[str, str]] = []
        for section in knowledge_sections:
            sources.append(
                {
                    "title": section.title,
                    "source": section.source,
                }
            )
        return sources

    def _extract_keywords(self, question: str) -> List[str]:
        tokens = re.findall(r"\w+", question.lower())
        keywords = [token for token in tokens if len(token) > 3]
        seen: Dict[str, None] = {}
        for keyword in keywords:
            if keyword not in seen:
                seen[keyword] = None
        return list(seen.keys())

    def _trim_excerpt(self, content: str) -> str:
        text = (content or "").strip()
        if len(text) <= 240:
            return text
        truncated = text[:237]
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]
        return truncated + "..."

    def _to_knowledge_section(self, document: Dict[str, Any]) -> KnowledgeSection:
        title = document.get("title") or document.get("id", "Documento")
        content = document.get("content", "")
        source = document.get("source", "memoria")
        return KnowledgeSection(
            title=title,
            excerpt=self._trim_excerpt(content),
            source=str(source),
        )

    def _should_offer_booking(self, question: str) -> bool:
        keywords = {
            "agendar",
            "horário",
            "horario",
            "disponível",
            "disponivel",
            "marcar",
            "consulta",
            "avaliação",
            "avaliacao",
            "sessão",
            "sessao",
        }
        lower_question = question.lower()
        return any(keyword in lower_question for keyword in keywords)

    async def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        if not self.enable_cache or not self.cache:
            return None
        return await self.cache.get_stats()

    async def getcache_stats(self) -> Optional[Dict[str, Any]]:  # pragma: no cover
        """Compatibilidade retroativa com chamadas legadas."""
        return await self.get_cache_stats()

    async def clear_cache(self) -> None:
        if self.enable_cache and self.cache:
            await self.cache.clear()

    async def clearcache(self) -> None:  # pragma: no cover
        """Compatibilidade retroativa com chamadas legadas."""
        await self.clear_cache()

    async def warm_cache(self, common_questions: List[str]) -> None:
        if not self.enable_cache or not self.cache:
            logger.warning("Não é possível aquecer o cache: recurso desabilitado")
            return
        for item in common_questions:
            try:
                await self.answer_question(item)
            except Exception as exc:  # noqa: BLE001
                logger.error("Erro ao aquecer cache para '%s': %s", item[:50], exc)

    async def warmcache(self, common_questions: List[str]) -> None:  # pragma: no cover
        """Compatibilidade retroativa com chamadas legadas."""
        await self.warm_cache(common_questions)

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
