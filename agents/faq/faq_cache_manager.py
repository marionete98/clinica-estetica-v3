"""
Cache Redis para respostas do agente de FAQ.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, Optional

from config.redis_client import RedisClient
from services.container import get_redis_client

logger = logging.getLogger(__name__)


class RedisFAQCache:
    """
    Cache distribuído para respostas do FAQ.
    """

    def __init__(
        self,
        redis_client: Optional[RedisClient] = None,
        ttl_seconds: int = 3600,
        max_size: int = 100,
    ):
        self._redis_client = redis_client or get_redis_client()
        self._ttl_seconds = ttl_seconds
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._prefix = "faq_cache:"

    def _normalize_question(self, question: str) -> str:
        normalized = question.lower().strip()
        replacements = {
            "quanto custa": "preço",
            "qual o valor": "preço",
            "qual valor": "preço",
            "quanto é": "preço",
            "quanto fica": "preço",
            "vocês fazem": "fazer",
            "vocês tem": "ter",
            "vocês trabalham com": "trabalhar",
            "pode fazer": "fazer",
            "posso fazer": "fazer",
        }
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        normalized = (
            normalized.replace("?", "")
            .replace("!", "")
            .replace(".", "")
            .replace("�", "")
        )
        return normalized

    def _generate_cache_key(self, question: str) -> str:
        normalized = self._normalize_question(question)
        digest = hashlib.md5(normalized.encode(), usedforsecurity=False).hexdigest()
        return f"{self._prefix}{digest}"

    async def get(self, question: str) -> Optional[Dict[str, Any]]:
        cache_key = self._generate_cache_key(question)
        try:
            value = await self._redis_client.get_value(cache_key, deserialize=True)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao ler cache do FAQ: %s", exc)
            return None

        if value is None:
            self._misses += 1
            return None

        self._hits += 1
        return value

    async def set(self, question: str, data: Dict[str, Any]) -> None:
        cache_key = self._generate_cache_key(question)
        try:
            await self._redis_client.set_value(
                cache_key, data, ttl=self._ttl_seconds
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao gravar cache do FAQ: %s", exc)

    async def clear(self) -> None:
        try:
            pattern = f"{self._prefix}*"
            keys = await self._redis_client.scan_keys(pattern)
            if keys:
                await self._redis_client.delete_keys(*keys)
            self._hits = 0
            self._misses = 0
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao limpar cache do FAQ: %s", exc)

    async def get_stats(self) -> Dict[str, Any]:
        try:
            pattern = f"{self._prefix}*"
            keys = await self._redis_client.scan_keys(pattern)
            size = len(keys)
        except Exception:  # noqa: BLE001
            size = None

        return {
            "ttl_seconds": self._ttl_seconds,
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "current_size": size,
        }


__all__ = ["RedisFAQCache"]
