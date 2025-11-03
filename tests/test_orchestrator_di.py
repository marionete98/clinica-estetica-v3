"""Regression tests for the orchestrator dependency-injection helpers."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from services.agent_orchestrator import AgentOrchestrator, create_orchestrator, orchestrator_lifespan


class TestOrchestratorFactory:
    """Validate the behaviour of the create_orchestrator helper."""

    @pytest.mark.asyncio
    async def test_create_orchestrator_produces_unique_instances(self) -> None:
        first = await create_orchestrator()
        second = await create_orchestrator()

        try:
            assert first is not second
            assert id(first) != id(second)
        finally:
            await first.cleanup()
            await second.cleanup()

    @pytest.mark.asyncio
    async def test_instances_do_not_share_agent_state(self) -> None:
        one = await create_orchestrator()
        two = await create_orchestrator()

        try:
            assert one.supervisor is not two.supervisor
            assert one.faq is not two.faq
            assert one.scheduler is not two.scheduler
        finally:
            await one.cleanup()
            await two.cleanup()


class TestOrchestratorLifespan:
    """Ensure the async context manager manages resources correctly."""

    @pytest.mark.asyncio
    async def test_lifespan_yields_configured_orchestrator(self) -> None:
        with patch("services.agent_orchestrator.AgentOrchestrator") as mock_ctor:
            instance = AsyncMock(spec=AgentOrchestrator)
            mock_ctor.return_value = instance

            async with orchestrator_lifespan() as orchestrator:
                assert orchestrator is instance

            instance.cleanup.assert_awaited_once()


class TestConcurrency:
    """Spot-check that concurrent orchestrators remain isolated."""

    @pytest.mark.asyncio
    async def test_concurrent_factory_calls(self) -> None:
        async def build_and_cleanup() -> int:
            orchestrator = await create_orchestrator()
            try:
                return id(orchestrator)
            finally:
                await orchestrator.cleanup()

        ids = await asyncio.gather(*(build_and_cleanup() for _ in range(10)))
        assert len(set(ids)) == len(ids)
