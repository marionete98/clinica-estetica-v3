"""
Tests for context managers and resource cleanup.

This module tests:
1. Orchestrator context manager (orchestrator_lifespan)
2. Redis client lazy initialization and cleanup
3. Memory leak prevention
4. Cleanup on exceptions
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import gc
import sys

from services.agent_orchestrator import orchestrator_lifespan, AgentOrchestrator
from config.redis_client import RedisClient


# ============================================================================
# ORCHESTRATOR CONTEXT MANAGER TESTS
# ============================================================================

class TestOrchestratorContextManager:
    """Test orchestrator_lifespan context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager_creates_and_cleans_up(self):
        """Test that context manager creates orchestrator and cleans up."""
        # Mock all agent creation functions
        with patch('services.agent_orchestrator.create_supervisor_agent'), \
             patch('services.agent_orchestrator.create_intake_agent'), \
             patch('services.agent_orchestrator.create_faq_agent'), \
             patch('services.agent_orchestrator.create_scheduler_agent'), \
             patch('services.agent_orchestrator.create_escalation_agent'):
            
            orchestrator_instance = None
            
            async with orchestrator_lifespan() as orchestrator:
                # Verify we got an orchestrator instance
                assert isinstance(orchestrator, AgentOrchestrator)
                orchestrator_instance = orchestrator
                
                # Mock cleanup method to verify it's called
                orchestrator.cleanup = AsyncMock()
            
            # Verify cleanup was called
            orchestrator_instance.cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_cleans_up_on_exception(self):
        """Test that cleanup happens even when exception occurs."""
        # Mock all agent creation functions
        with patch('services.agent_orchestrator.create_supervisor_agent'), \
             patch('services.agent_orchestrator.create_intake_agent'), \
             patch('services.agent_orchestrator.create_faq_agent'), \
             patch('services.agent_orchestrator.create_scheduler_agent'), \
             patch('services.agent_orchestrator.create_escalation_agent'):
            
            orchestrator_instance = None
            
            with pytest.raises(ValueError, match="Test exception"):
                async with orchestrator_lifespan() as orchestrator:
                    orchestrator_instance = orchestrator
                    orchestrator.cleanup = AsyncMock()
                    
                    # Raise exception to test cleanup
                    raise ValueError("Test exception")
            
            # Verify cleanup was still called despite exception
            orchestrator_instance.cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_handles_cleanup_errors(self):
        """Test that cleanup errors don't crash the context manager."""
        # Mock all agent creation functions
        with patch('services.agent_orchestrator.create_supervisor_agent'), \
             patch('services.agent_orchestrator.create_intake_agent'), \
             patch('services.agent_orchestrator.create_faq_agent'), \
             patch('services.agent_orchestrator.create_scheduler_agent'), \
             patch('services.agent_orchestrator.create_escalation_agent'):
            
            async with orchestrator_lifespan() as orchestrator:
                # Mock cleanup to raise an error
                orchestrator.cleanup = AsyncMock(side_effect=Exception("Cleanup error"))
            
            # Should not raise - cleanup errors are caught and logged
    
    @pytest.mark.asyncio
    async def test_context_manager_multiple_instances(self):
        """Test that multiple context managers create isolated instances."""
        # Mock all agent creation functions
        with patch('services.agent_orchestrator.create_supervisor_agent'), \
             patch('services.agent_orchestrator.create_intake_agent'), \
             patch('services.agent_orchestrator.create_faq_agent'), \
             patch('services.agent_orchestrator.create_scheduler_agent'), \
             patch('services.agent_orchestrator.create_escalation_agent'):
            
            async with orchestrator_lifespan() as orch1:
                async with orchestrator_lifespan() as orch2:
                    # Verify they are different instances
                    assert orch1 is not orch2
                    assert id(orch1) != id(orch2)


# ============================================================================
# REDIS CLIENT LAZY INITIALIZATION TESTS
# ============================================================================

class TestRedisClientLazyInitialization:
    """Test Redis client lazy initialization and cleanup."""
    
    @pytest.mark.asyncio
    async def test_redis_client_lazy_initialization(self):
        """Test that Redis client initializes lazily on first use."""
        client = RedisClient()
        
        # Should not be initialized yet
        assert client._initialized is False
        assert client._client is None
        
        # Mock the Redis connection
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            # Initialize
            await client.ensure_initialized()
            
            # Should now be initialized
            assert client._initialized is True
            assert client._client is not None
            mock_redis.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_client_ensure_initialized_idempotent(self):
        """Test that ensure_initialized can be called multiple times safely."""
        client = RedisClient()
        
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            # Call multiple times
            await client.ensure_initialized()
            await client.ensure_initialized()
            await client.ensure_initialized()
            
            # Should only initialize once
            assert mock_from_url.call_count == 1
            assert mock_redis.ping.call_count == 1
    
    @pytest.mark.asyncio
    async def test_redis_client_close(self):
        """Test that Redis client closes properly."""
        client = RedisClient()
        
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_redis.close = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            # Initialize and close
            await client.ensure_initialized()
            await client.close()
            
            # Should be closed
            mock_redis.close.assert_called_once()
            assert client._initialized is False
            assert client._client is None
    
    @pytest.mark.asyncio
    async def test_redis_client_property_raises_before_init(self):
        """Test that client property raises error before initialization."""
        client = RedisClient()
        
        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            _ = client.client
    
    @pytest.mark.asyncio
    async def test_redis_client_methods_auto_initialize(self):
        """Test that Redis methods auto-initialize the client."""
        client = RedisClient()
        
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_redis.get = AsyncMock(return_value=None)
            mock_from_url.return_value = mock_redis
            
            # Call a method without manually initializing
            await client.get_value("test_key")
            
            # Should have auto-initialized
            assert client._initialized is True
            mock_redis.ping.assert_called_once()
            mock_redis.get.assert_called_once_with("test_key")


# ============================================================================
# MEMORY LEAK TESTS
# ============================================================================

class TestMemoryLeaks:
    """Test for memory leaks in context managers and cleanup."""
    
    @pytest.mark.asyncio
    async def test_no_memory_leak_with_context_manager(self):
        """Test that using context manager 100 times doesn't leak memory."""
        # Mock all agent creation functions
        with patch('services.agent_orchestrator.create_supervisor_agent'), \
             patch('services.agent_orchestrator.create_intake_agent'), \
             patch('services.agent_orchestrator.create_faq_agent'), \
             patch('services.agent_orchestrator.create_scheduler_agent'), \
             patch('services.agent_orchestrator.create_escalation_agent'):

            # Warm up - run once to initialize any caches
            async with orchestrator_lifespan() as orchestrator:
                orchestrator.cleanup = AsyncMock()

            # Force garbage collection
            gc.collect()

            # Track object count after warmup
            initial_objects = len(gc.get_objects())

            # Create and cleanup 100 orchestrators
            for _ in range(100):
                async with orchestrator_lifespan() as orchestrator:
                    # Mock cleanup
                    orchestrator.cleanup = AsyncMock()
                    pass

            # Force garbage collection
            gc.collect()

            # Check object count after
            final_objects = len(gc.get_objects())

            # Allow reasonable growth for Python's internal caching
            # The key is that growth should be sub-linear, not proportional to iterations
            # With 100 iterations, we expect < 5000 new objects (not 100x growth)
            growth = final_objects - initial_objects
            assert growth < 5000, f"Possible memory leak: {growth} new objects after 100 iterations"
    
    @pytest.mark.asyncio
    async def test_redis_client_cleanup_releases_resources(self):
        """Test that Redis client cleanup releases resources."""
        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_redis.close = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            # Create 10 clients and close them
            for _ in range(10):
                client = RedisClient()
                await client.ensure_initialized()
                await client.close()
            
            # Verify close was called 10 times
            assert mock_redis.close.call_count == 10
    
    @pytest.mark.asyncio
    async def test_orchestrator_cleanup_on_exception_prevents_leaks(self):
        """Test that cleanup happens even with exceptions, preventing leaks."""
        # Mock all agent creation functions
        with patch('services.agent_orchestrator.create_supervisor_agent'), \
             patch('services.agent_orchestrator.create_intake_agent'), \
             patch('services.agent_orchestrator.create_faq_agent'), \
             patch('services.agent_orchestrator.create_scheduler_agent'), \
             patch('services.agent_orchestrator.create_escalation_agent'):
            
            cleanup_count = 0
            
            # Create 50 orchestrators with exceptions
            for i in range(50):
                try:
                    async with orchestrator_lifespan() as orchestrator:
                        # Mock cleanup to count calls
                        original_cleanup = orchestrator.cleanup
                        
                        async def counting_cleanup():
                            nonlocal cleanup_count
                            cleanup_count += 1
                        
                        orchestrator.cleanup = counting_cleanup
                        
                        # Raise exception every other iteration
                        if i % 2 == 0:
                            raise ValueError("Test exception")
                except ValueError:
                    pass
            
            # Verify cleanup was called for all 50 iterations
            assert cleanup_count == 50, f"Cleanup called {cleanup_count} times, expected 50"


# ============================================================================
# CONCURRENT ACCESS TESTS
# ============================================================================

class TestConcurrentAccess:
    """Test concurrent access to context managers."""
    
    @pytest.mark.asyncio
    async def test_concurrent_context_managers(self):
        """Test that multiple concurrent context managers work correctly."""
        # Mock all agent creation functions
        with patch('services.agent_orchestrator.create_supervisor_agent'), \
             patch('services.agent_orchestrator.create_intake_agent'), \
             patch('services.agent_orchestrator.create_faq_agent'), \
             patch('services.agent_orchestrator.create_scheduler_agent'), \
             patch('services.agent_orchestrator.create_escalation_agent'):
            
            async def use_orchestrator(index: int):
                async with orchestrator_lifespan() as orchestrator:
                    orchestrator.cleanup = AsyncMock()
                    # Simulate some work
                    await asyncio.sleep(0.01)
                    return index
            
            # Run 20 concurrent orchestrators
            results = await asyncio.gather(*[use_orchestrator(i) for i in range(20)])
            
            # Verify all completed successfully
            assert results == list(range(20))

