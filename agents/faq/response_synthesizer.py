"""
Funções auxiliares para pós-processamento de respostas do FAQ.
"""

from __future__ import annotations

from typing import List, Tuple


def normalize_response(raw_output: str) -> str:
    text = raw_output.strip()
    if text.startswith("Knowledge Base Results:"):
        return _synthesize_from_kb(text)
    return text


def strip_low_confidence_marker(text: str) -> Tuple[str, bool]:
    marker = "ESCALATE_LOW_CONFIDENCE"
    if marker not in text:
        return text, False
    cleaned = text.replace(marker, "").strip()
    return cleaned, True


def _synthesize_from_kb(raw_output: str) -> str:
    treatments: List[str] = []
    for line in raw_output.splitlines():
        if line and line[0].isdigit() and "." in line:
            treatments.append(line.split(".", 1)[1].strip())
    if treatments:
        bullets = "\n".join(f"✨ {item}" for item in treatments)
        return (
            "Olá! 😊 Oferecemos diversos tratamentos estéticos:\n\n"
            f"{bullets}\n\n"
            "Quer saber mais sobre algum procedimento específico? Posso ajudar a agendar!"
        )
    return (
        "Olá! 😊 Oferecemos diversos tratamentos estéticos. "
        "Gostaria de saber sobre algum procedimento específico?"
    )


__all__ = ["normalize_response", "strip_low_confidence_marker"]
