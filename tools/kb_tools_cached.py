"""
Cached Knowledge Base tools backed by the KnowledgeBaseCacheService.

This module exposes async helpers that align with AutoGen's memory guidance:
- All KB lookups flow through a dedicated cache service (Redis-backed memory)
- Message templates and formatting leverage the same service for consistency
"""

from typing import Dict, Any, Optional
import logging

from services.container import get_kb_cache_service

logger = logging.getLogger(__name__)


async def search_knowledge_base(
    query: str,
    top_k: int = 3,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search the knowledge base cache using the centralized service and return a
    JSON-friendly dictionary containing the entries and their titles.
    """
    if not query or not query.strip():
        logger.warning("Empty query provided to search_knowledge_base")
        return {"entries": [], "sources": []}

    if top_k < 1:
        logger.warning(f"Invalid top_k value: {top_k}, using default of 3")
        top_k = 3

    cache_service = get_kb_cache_service()
    results = await cache_service.search_knowledge_base(query, top_k, category)
    sources = [
        entry.get("title") or entry.get("id", "KB Entry")
        for entry in results
    ]
    return {
        "entries": results,
        "sources": sources,
    }


async def get_message_template(template_name: str) -> Optional[Dict[str, Any]]:
    """Retrieve a cached message template by name."""
    if not template_name or not template_name.strip():
        logger.warning("Empty template_name provided to get_message_template")
        return None

    cache_service = get_kb_cache_service()
    return await cache_service.get_message_template(template_name)


async def format_template(
    template_name: str,
    variables: Dict[str, str],
) -> Optional[str]:
    """Format a cached template with the provided variables."""
    cache_service = get_kb_cache_service()
    return await cache_service.format_template(template_name, variables)


async def get_cache_statistics() -> Dict[str, Any]:
    """Expose knowledge base cache statistics."""
    cache_service = get_kb_cache_service()
    stats = await cache_service.get_cache_stats()
    return {
        "total_entries": stats.total_entries,
        "total_templates": stats.total_templates,
        "last_sync": stats.last_sync.isoformat() if stats.last_sync else None,
        "cache_hits": stats.cache_hits,
        "cache_misses": stats.cache_misses,
        "hit_rate": stats.hit_rate,
        "cache_size_mb": stats.cache_size_mb,
    }
