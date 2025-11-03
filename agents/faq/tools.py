"""
Funções utilitárias para registrar ferramentas do agente de FAQ.
"""

from __future__ import annotations

import json
import logging
from typing import List

from autogen_core.tools import FunctionTool

from tools.kb_tools_cached import (
    format_template,
    get_message_template,
    search_knowledge_base,
)

logger = logging.getLogger(__name__)


def build_tools() -> List[FunctionTool]:
    async def search_knowledge_base_tool(query: str) -> str:
        result = await search_knowledge_base(query=query, top_k=10, category=None)
        entries = result.get("entries", [])
        if not entries:
            return "No results found in knowledge base."

        formatted_lines = ["Knowledge Base Results:"]
        for idx, entry in enumerate(entries[:10], 1):
            title = entry.get("title", "Untitled")
            content = entry.get("content", "No content")
            formatted_lines.append(f"\n{idx}. {title}")
            formatted_lines.append(f"   {content}")
        return "\n".join(formatted_lines)

    async def get_message_template_tool(template_name: str) -> str:
        result = await get_message_template(template_name)
        return json.dumps(result)

    async def format_template_tool(template_name: str, variables_json: str) -> str:
        try:
            variables = json.loads(variables_json) if variables_json else {}
        except json.JSONDecodeError:
            logger.error("Invalid JSON em format_template_tool: %s", variables_json)
            return json.dumps(None)

        result = await format_template(template_name, variables)
        return json.dumps(result) if result else json.dumps(None)

    return [
        FunctionTool(
            search_knowledge_base_tool,
            description=(
                "Busca conteúdos relevantes na base de conhecimento da clínica "
                "para responder dúvidas dos pacientes."
            ),
        ),
        FunctionTool(
            get_message_template_tool,
            description=(
                "Recupera templates de mensagens padronizadas, garantindo consistência."
            ),
        ),
        FunctionTool(
            format_template_tool,
            description=(
                "Aplica variáveis em templates retornando o texto formatado para envio."
            ),
        ),
    ]


__all__ = ["build_tools"]
