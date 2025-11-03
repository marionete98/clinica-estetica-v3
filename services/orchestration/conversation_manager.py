"""
Gerencia o histórico de conversas armazenado no Redis.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ConversationManager:
    def __init__(self, redis_client: Any) -> None:
        self._redis = redis_client

    async def load_context(
        self, conversation_id: str, max_messages: int
    ) -> List[Dict[str, str]]:
        """
        Recupera as últimas mensagens do contexto de uma conversa.
        """
        try:
            messages = await self._redis.get_context(
                conversation_id, max_messages=max_messages
            )
            if messages:
                logger.info(
                    "Contexto carregado do Redis: conv_id=%s, mensagens=%s",
                    conversation_id,
                    len(messages),
                )
            else:
                logger.info(
                    "Nenhum contexto encontrado no Redis para conv_id=%s",
                    conversation_id,
                )
            return messages or []
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Falha ao carregar contexto do Redis para conv_id=%s: %s",
                conversation_id,
                exc,
            )
            return []

    async def append_context(
        self, conversation_id: str, user_message: str, assistant_response: str
    ) -> None:
        """
        Persiste a última interação (mensagem do usuário + resposta do agente).
        """
        try:
            await self._redis.append_message(
                conversation_id, role="user", content=user_message
            )
            await self._redis.append_message(
                conversation_id, role="assistant", content=assistant_response
            )
            logger.info(
                "Contexto atualizado no Redis para conv_id=%s", conversation_id
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Falha ao atualizar contexto no Redis para conv_id=%s: %s",
                conversation_id,
                exc,
                exc_info=True,
            )


__all__ = ["ConversationManager"]
