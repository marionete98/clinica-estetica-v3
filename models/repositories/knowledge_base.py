"""
Knowledge base and message template repository operations.
"""

from __future__ import annotations

from typing import List, Optional

from services.container import get_supabase_client
from models.database import KnowledgeBase, MessageTemplate


async def search_knowledge_base(
    keywords: List[str], category: Optional[str] = None
) -> List[KnowledgeBase]:
    """
    Search knowledge base entries using simple keyword overlap.
    """
    supabase = get_supabase_client().client

    query = supabase.table("knowledge_base").select("*").eq("active", True)

    if category:
        query = query.eq("category", category)

    response = query.execute()

    results: List[KnowledgeBase] = []
    for kb_data in response.data:
        kb = KnowledgeBase(**kb_data)
        if kb.keywords:
            for keyword in keywords:
                if any(keyword.lower() in kw.lower() for kw in kb.keywords):
                    results.append(kb)
                    break

    return results


async def get_message_template(name: str) -> Optional[MessageTemplate]:
    """
    Retrieve message template by name.
    """
    supabase = get_supabase_client().client

    response = (
        supabase.table("message_templates")
        .select("*")
        .eq("name", name)
        .eq("active", True)
        .execute()
    )

    if response.data and len(response.data) > 0:
        return MessageTemplate(**response.data[0])
    return None


__all__ = ["search_knowledge_base", "get_message_template"]
