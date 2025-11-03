"""
Test main.py shutdown handler and resource cleanup.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_lifespan_shutdown_calls_cleanup():
    """Test that lifespan shutdown handler calls cleanup_orchestrator."""
    
    with patch('main.cleanup_orchestrator', new_callable=AsyncMock) as mock_cleanup, \
         patch('main.get_redis_client') as mock_get_redis, \
         patch('main.get_supabase_client') as mock_get_supabase, \
         patch('main.chatwoot_client') as mock_chatwoot, \
         patch('main.AsyncIOScheduler') as mock_scheduler_class:
        
        # Setup mocks
        redis_client = MagicMock()
        redis_client.ensure_initialized = AsyncMock()
        mock_get_redis.return_value = redis_client

        supabase_client = MagicMock()
        supabase_client.client.table.return_value.select.return_value.limit.return_value.execute.return_value = []
        mock_get_supabase.return_value = supabase_client

        mock_chatwoot.health_check.return_value = True
        mock_chatwoot.close.return_value = None
        
        mock_scheduler = MagicMock()
        mock_scheduler.shutdown = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        # Import app after patching
        from main import app
        
        # Create test client (triggers lifespan)
        with TestClient(app) as client:
            # Make a simple request to ensure app is running
            response = client.get("/")
            assert response.status_code == 200
        
        # After context exit, shutdown should have been called
        mock_cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_shutdown_handles_cleanup_errors():
    """Test that lifespan shutdown handles cleanup errors gracefully."""
    
    with patch('main.cleanup_orchestrator', new_callable=AsyncMock) as mock_cleanup, \
         patch('main.redis_client') as mock_redis, \
         patch('main.supabase_client') as mock_supabase, \
         patch('main.chatwoot_client') as mock_chatwoot, \
         patch('main.AsyncIOScheduler') as mock_scheduler_class, \
         patch('main.logger') as mock_logger:
        
        # Setup mocks
        mock_redis.client.ping.return_value = True
        mock_supabase.client.table.return_value.select.return_value.limit.return_value.execute.return_value = []
        mock_chatwoot.health_check.return_value = True
        mock_chatwoot.close.return_value = None
        
        mock_scheduler = MagicMock()
        mock_scheduler.shutdown = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        # Make cleanup raise an error
        mock_cleanup.side_effect = Exception("Cleanup failed")
        
        # Import app after patching
        from main import app
        
        # Create test client - should not raise exception
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
        
        # Verify cleanup was attempted
        mock_cleanup.assert_called_once()
        
        # Verify error was logged
        mock_logger.error.assert_any_call(
            "Error cleaning up agent orchestrator: Cleanup failed"
        )


def test_cleanup_orchestrator_imported():
    """Test that cleanup_orchestrator is properly imported in main.py."""
    
    import main
    
    # Verify cleanup_orchestrator is imported
    assert hasattr(main, 'cleanup_orchestrator'), "cleanup_orchestrator not imported in main.py"
    assert callable(main.cleanup_orchestrator), "cleanup_orchestrator is not callable"


@pytest.mark.asyncio
async def test_scheduler_shutdown_on_lifespan_end():
    """Test that APScheduler is shut down during lifespan shutdown."""
    
    with patch('main.cleanup_orchestrator', new_callable=AsyncMock), \
         patch('main.redis_client') as mock_redis, \
         patch('main.supabase_client') as mock_supabase, \
         patch('main.chatwoot_client') as mock_chatwoot, \
         patch('main.AsyncIOScheduler') as mock_scheduler_class:
        
        # Setup mocks
        mock_redis.client.ping.return_value = True
        mock_supabase.client.table.return_value.select.return_value.limit.return_value.execute.return_value = []
        mock_chatwoot.health_check.return_value = True
        mock_chatwoot.close.return_value = None
        
        mock_scheduler = MagicMock()
        mock_scheduler.shutdown = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        # Import app after patching
        from main import app
        
        # Create test client
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
        
        # Verify scheduler shutdown was called
        mock_scheduler.shutdown.assert_called_once_with(wait=True)


@pytest.mark.asyncio
async def test_chatwoot_client_closed_on_shutdown():
    """Test that Chatwoot client is closed during shutdown."""
    
    with patch('main.cleanup_orchestrator', new_callable=AsyncMock), \
         patch('main.redis_client') as mock_redis, \
         patch('main.supabase_client') as mock_supabase, \
         patch('main.chatwoot_client') as mock_chatwoot, \
         patch('main.AsyncIOScheduler') as mock_scheduler_class:
        
        # Setup mocks
        mock_redis.client.ping.return_value = True
        mock_supabase.client.table.return_value.select.return_value.limit.return_value.execute.return_value = []
        mock_chatwoot.health_check.return_value = True
        mock_chatwoot.close = MagicMock()
        
        mock_scheduler = MagicMock()
        mock_scheduler.shutdown = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        # Import app after patching
        from main import app
        
        # Create test client
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
        
        # Verify Chatwoot client close was called
        mock_chatwoot.close.assert_called_once()
