"""Parsers utilitários para respostas do scheduler."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from agents.scheduler.slot_finder import format_slots_response
from utils.response_parser import parse_messages_from_run_result

logger = logging.getLogger(__name__)


def parse_run_result(run_result: Any) -> Dict[str, Any]:
    """
    Converte o resultado do AutoGen em um dicionário padronizado.
    """
    try:
        action_obj = run_result.messages[-1].content
        if hasattr(action_obj, "action"):
            return {
                "response": action_obj.response,
                "action": action_obj.action,
                "requires_confirmation": bool(action_obj.requires_confirmation),
                "booking_id": getattr(action_obj, "booking_id", None),
                "structured": True,
            }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao ler saída estruturada do scheduler: %s", exc)

    fallback_text = parse_messages_from_run_result(run_result, "scheduler")
    return _fallback_payload(fallback_text)


def _fallback_payload(text: str) -> Dict[str, Any]:
    cleaned = text or ""
    if cleaned.strip().startswith("[{"):
        slots = _parse_slots(cleaned)
        if slots:
            cleaned = format_slots_response(slots)
    else:
        cleaned = cleaned.strip()

    return {
        "response": cleaned,
        "action": "info_provided",
        "requires_confirmation": False,
        "booking_id": None,
        "structured": False,
    }


def _parse_slots(raw: str) -> Optional[list]:
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else None
    except json.JSONDecodeError:
        return None


__all__ = ["parse_run_result"]
