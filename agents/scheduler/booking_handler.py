"""Payload helpers for Scheduler agent responses."""

from __future__ import annotations

from typing import Dict

from utils.error_handlers import ErrorRecoveryStrategy, ErrorType, get_fallback_response


_SCHEDULING_KEYWORDS = {
    "agendar",
    "remarcar",
    "cancelar",
    "horário",
    "horarios",
    "agenda",
    "marcar",
    "consulta",
}

_RESPONSE_HINTS = {
    "horário",
    "horarios",
    "agenda",
    "disponível",
}


def missing_contact_payload(phone: str) -> Dict[str, object]:
    return {
        "response": (
            "Percebi que ainda não temos um cadastro confirmado para você. "
            "Vou acionar nossa equipe para concluir o agendamento com segurança, tudo bem?"
        ),
        "action": "escalate_missing_contact",
        "booking_id": None,
        "requires_confirmation": False,
        "should_escalate": True,
        "metadata": {
            "reason": "missing_contact_id",
            "phone": phone,
        },
    }


def ensure_scheduling_hint(user_message: str, response_text: str) -> str:
    lower_user = user_message.lower()
    if not any(keyword in lower_user for keyword in _SCHEDULING_KEYWORDS):
        return response_text

    if any(keyword in response_text.lower() for keyword in _RESPONSE_HINTS):
        return response_text

    return (
        response_text.rstrip()
        + "\n\nPosso verificar a agenda e horários disponíveis para você."
    )


def build_success_payload(parsed: Dict[str, object]) -> Dict[str, object]:
    return {
        "response": parsed["response"],
        "action": parsed["action"],
        "booking_id": parsed.get("booking_id"),
        "requires_confirmation": parsed.get("requires_confirmation", False),
    }


def validation_error_payload() -> Dict[str, object]:
    fallback = get_fallback_response(ErrorType.UNCLEAR_REQUEST)
    return {
        "response": fallback,
        "action": "error",
        "booking_id": None,
        "requires_confirmation": False,
        "error_type": ErrorType.UNCLEAR_REQUEST.value,
    }


def unknown_error_payload() -> Dict[str, object]:
    err_type = ErrorType.UNKNOWN_ERROR
    fallback = get_fallback_response(err_type)
    recovery = ErrorRecoveryStrategy.get_recovery_action(err_type)
    return {
        "response": fallback,
        "action": "error",
        "booking_id": None,
        "requires_confirmation": False,
        "error_type": err_type.value,
        "recovery_action": recovery,
        "should_escalate": recovery == "escalate_to_human",
    }


__all__ = [
    "missing_contact_payload",
    "ensure_scheduling_hint",
    "build_success_payload",
    "validation_error_payload",
    "unknown_error_payload",
]
