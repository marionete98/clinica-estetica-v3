from __future__ import annotations

from typing import List, Optional

from models.repositories.knowledge_base import (
    get_message_template,
    search_knowledge_base,
)
from models.database import KnowledgeBase, MessageTemplate


class KnowledgeBaseRepository:
    async def search(
        self, keywords: List[str], category: Optional[str] = None
    ) -> List[KnowledgeBase]:
        return await search_knowledge_base(keywords, category)


class TemplateRepository:
    async def get(self, name: str) -> Optional[MessageTemplate]:
        return await get_message_template(name)


__all__ = ["KnowledgeBaseRepository", "TemplateRepository"]
