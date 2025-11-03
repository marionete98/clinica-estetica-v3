"""
Redis-backed knowledge memory wrapper aligned with AutoGen memory guidance.

This adapter exposes a simple Memory-like interface (`add`, `query`,
`update_context`, `clear`, `close`) while delegating storage and search
responsibilities to the existing `KnowledgeBaseCacheService`.
"""

from typing import List, Dict, Any, Optional
import logging

from services.container import get_kb_cache_service, get_redis_client
from services.kb_cache_service import KnowledgeBaseCacheService
from config.redis_client import RedisClient

logger = logging.getLogger(__name__)


class RedisKnowledgeMemory:
    """Thin wrapper that presents the KB cache as an AutoGen-compatible memory."""

    def __init__(
        self,
        default_top_k: int = 3,
        cache_service: Optional[KnowledgeBaseCacheService] = None,
        redis_client: Optional[RedisClient] = None,
    ):
        self.default_top_k = default_top_k
        self._cache_service = cache_service or get_kb_cache_service()
        self._redis_client = redis_client or get_redis_client()

    async def add(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Add or update documents in the knowledge memory.

        Each document should at minimum contain: id, title, content.
        """
        return await self._cache_service.upsert_entries(documents)

    async def query(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query knowledge documents using the same scoring logic as the cache service.
        """
        category = metadata.get("category") if metadata else None
        return await self._cache_service.search_knowledge_base(
            query,
            top_k=top_k or self.default_top_k,
            category=category,
        )

    async def update_context(
        self,
        conversation_id: str,
        messages: List[Dict[str, str]],
    ) -> None:
        """
        Persist conversation context alongside knowledge hits.
        """
        await self._redis_client.set_context(conversation_id, messages)

    async def clear(self, *, conversation_id: Optional[str] = None) -> None:
        """
        Reset memory for a specific conversation or the entire KB cache.
        """
        if conversation_id:
            await self._redis_client.clear_context(conversation_id)
        else:
            await self._cache_service.invalidate_cache()

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge documents (alias for query method for compatibility).
        
        Args:
            query: Search query string
            top_k: Number of results to return
            category: Optional category filter
            
        Returns:
            List of matching documents
        """
        metadata = {"category": category} if category else None
        return await self.query(query, top_k=top_k, metadata=metadata)

    async def close(self) -> None:
        """Placeholder for API parity; no resources to release explicitly."""
        # The underlying redis client is managed by the application lifecycle.
        return
