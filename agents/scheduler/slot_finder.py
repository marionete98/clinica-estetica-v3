"""Utilitário para formatar sugestões de horários disponíveis."""

from __future__ import annotations

from typing import Dict, List


def format_slots_response(slots: List[Dict[str, str]]) -> str:
    if not slots:
        return (
            "Desculpe, não encontrei horários disponíveis para essa data. "
            "Gostaria de verificar outra data?"
        )

    lines = [
        f"Olá! 😊 Encontrei {len(slots)} horários disponíveis:",
        "",
    ]

    for idx, slot in enumerate(slots[:5], 1):
        date = slot.get("date", "data não informada")
        start = slot.get("start_time", "horário não informado")
        lines.append(f"✨ Opção {idx}: {date} às {start}")

    lines.append("")
    lines.append("Qual horário você prefere? Posso confirmar o agendamento para você!")
    return "\n".join(lines)


__all__ = ["format_slots_response"]
