"""Simple benchmark runner for the refactored orchestrator."""

from __future__ import annotations

import asyncio
import time
from statistics import mean, stdev
from typing import List, Tuple


class _StubOrchestrator:
    """Fallback orchestrator used when runtime dependencies are missing."""

    async def orchestrate(self, conversation_id: str, phone: str, message: str) -> dict:
        await asyncio.sleep(0.05)
        return {
            "conversation_id": conversation_id,
            "phone": phone,
            "message": message,
            "agent": "stub",
            "response": "Stubbed response",
        }

    async def cleanup(self) -> None:  # pragma: no cover - trivial
        return None


async def _create_orchestrator() -> Tuple[object, bool]:
    try:
        from services.agent_orchestrator import create_orchestrator as _real_factory

        orchestrator = await _real_factory()
        return orchestrator, True
    except ModuleNotFoundError:
        return _StubOrchestrator(), False


async def benchmark_orchestrator(messages: List[str]) -> None:
    orchestrator, using_real_stack = await _create_orchestrator()

    try:
        timings = []
        for msg in messages:
            start = time.perf_counter()
            await orchestrator.orchestrate(
                conversation_id="bench-123",
                phone="+5511999999999",
                message=msg,
            )
            elapsed = time.perf_counter() - start
            timings.append(elapsed)
            print(f"{msg[:32]} -> {elapsed * 1000:.2f} ms")

        if timings:
            print("Stack: real" if using_real_stack else "Stack: stub")
            print()
            print(f"Média: {mean(timings) * 1000:.2f} ms")
            if len(timings) > 1:
                print(f"Desvio padrão: {stdev(timings) * 1000:.2f} ms")
            print(f"Min: {min(timings) * 1000:.2f} ms")
            print(f"Max: {max(timings) * 1000:.2f} ms")
    finally:
        await orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(
        benchmark_orchestrator(
            [
                "Olá!",
                "Quanto custa depilação a laser?",
                "Quero agendar para amanhã",
                "Qual horário disponível?",
            ]
        )
    )
