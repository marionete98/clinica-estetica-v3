from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_lifespan_shutdown_runs_without_agent_cleanup() -> None:
    with (
        patch("main.get_redis_client") as mock_get_redis,
        patch("main.get_supabase_client") as mock_get_supabase,
        patch("main.chatwoot_client") as mock_chatwoot,
        patch("main.AsyncIOScheduler") as mock_scheduler_class,
    ):
        redis_client = MagicMock()
        redis_client.ensure_initialized = AsyncMock()
        mock_get_redis.return_value = redis_client

        supabase_client = MagicMock()
        supabase_client.client.table.return_value.select.return_value.limit.return_value.execute.return_value = []
        mock_get_supabase.return_value = supabase_client

        mock_chatwoot.health_check.return_value = True
        mock_chatwoot.close = MagicMock()

        scheduler = MagicMock()
        scheduler.shutdown = MagicMock()
        mock_scheduler_class.return_value = scheduler

        from main import app

        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200

        scheduler.shutdown.assert_called_once_with(wait=True)
        mock_chatwoot.close.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_shutdown_logs_scheduler_errors() -> None:
    with (
        patch("main.get_redis_client") as mock_get_redis,
        patch("main.get_supabase_client") as mock_get_supabase,
        patch("main.chatwoot_client") as mock_chatwoot,
        patch("main.AsyncIOScheduler") as mock_scheduler_class,
        patch("main.logger") as mock_logger,
    ):
        redis_client = MagicMock()
        redis_client.ensure_initialized = AsyncMock()
        mock_get_redis.return_value = redis_client

        supabase_client = MagicMock()
        supabase_client.client.table.return_value.select.return_value.limit.return_value.execute.return_value = []
        mock_get_supabase.return_value = supabase_client

        mock_chatwoot.health_check.return_value = True
        mock_chatwoot.close = MagicMock()

        scheduler = MagicMock()
        scheduler.shutdown.side_effect = Exception("boom")
        mock_scheduler_class.return_value = scheduler

        from main import app

        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200

        mock_logger.error.assert_any_call("Error shutting down scheduler: boom")
