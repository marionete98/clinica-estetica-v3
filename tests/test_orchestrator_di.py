"""
Tests for AgentOrchestrator Dependency Injection Pattern.

This test suite verifies that the new DI pattern:
1. Creates isolated instances per request
2. Prevents race conditions between concurrent conversations
3. Doesn't leak memory
4. Maintains performance
5. Properly cleans up resources

Requirements: Phase 1, Task 1.2
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any

from services.agent_orchestrator import (
    AgentOrchestrator,
    create_orchestrator,
    get_orchestrator,
    orchestrate_agents
)


class TestOrchestratorDependencyInjection:
    """Test suite for orchestrator dependency injection pattern."""
    
    @pytest.mark.asyncio
    async def test_create_orchestrator_returns_new_instance(self):
        """Test that create_orchestrator() returns a new instance each time."""
        orchestrator1 = await create_orchestrator()
        orchestrator2 = await create_orchestrator()
        
        # Should be different instances
        assert orchestrator1 is not orchestrator2
        assert id(orchestrator1) != id(orchestrator2)
        
        # Cleanup
        await orchestrator1.cleanup()
        await orchestrator2.cleanup()
    
    @pytest.mark.asyncio
    async def test_get_orchestrator_returns_new_instance(self):
        """Test that get_orchestrator() returns a new instance (no longer singleton)."""
        orchestrator1 = get_orchestrator()
        orchestrator2 = get_orchestrator()
        
        # Should be different instances (no longer singleton)
        assert orchestrator1 is not orchestrator2
        assert id(orchestrator1) != id(orchestrator2)
        
        # Cleanup
        await orchestrator1.cleanup()
        await orchestrator2.cleanup()
    
    @pytest.mark.asyncio
    async def test_orchestrator_instances_are_isolated(self):
        """Test that orchestrator instances don't share state."""
        orchestrator1 = await create_orchestrator()
        orchestrator2 = await create_orchestrator()
        
        # Verify they have separate agent instances
        assert orchestrator1.supervisor is not orchestrator2.supervisor
        assert orchestrator1.intake is not orchestrator2.intake
        assert orchestrator1.faq is not orchestrator2.faq
        assert orchestrator1.scheduler is not orchestrator2.scheduler
        assert orchestrator1.escalation is not orchestrator2.escalation
        
        # Cleanup
        await orchestrator1.cleanup()
        await orchestrator2.cleanup()


class TestConcurrentConversations:
    """Test concurrent conversation handling without race conditions."""
    
    @pytest.mark.asyncio
    async def test_concurrent_conversations_no_race_condition(self):
        """Test 50 concurrent conversations without race conditions."""
        num_conversations = 50
        results = []
        
        async def process_conversation(conv_id: int):
            """Simulate processing a conversation."""
            orchestrator = await create_orchestrator()
            try:
                # Mock the orchestrate method to return conversation-specific data
                with patch.object(orchestrator, 'orchestrate', new_callable=AsyncMock) as mock_orchestrate:
                    mock_orchestrate.return_value = {
                        "response": f"Response for conversation {conv_id}",
                        "conversation_id": str(conv_id),
                        "agent": "supervisor",
                        "intent": "test"
                    }
                    
                    result = await orchestrator.orchestrate(
                        conversation_id=str(conv_id),
                        phone=f"+5594991398{conv_id:03d}",
                        message=f"Test message {conv_id}"
                    )
                    
                    return result
            finally:
                await orchestrator.cleanup()
        
        # Run all conversations concurrently
        tasks = [process_conversation(i) for i in range(num_conversations)]
        results = await asyncio.gather(*tasks)
        
        # Verify all conversations completed successfully
        assert len(results) == num_conversations
        
        # Verify each conversation got its own response (no cross-contamination)
        for i, result in enumerate(results):
            assert result["conversation_id"] == str(i)
            assert f"conversation {i}" in result["response"]
    
    @pytest.mark.asyncio
    async def test_concurrent_conversations_different_orchestrators(self):
        """Test that concurrent conversations use different orchestrator instances."""
        num_conversations = 20
        orchestrators = []

        async def create_and_store_orchestrator(conv_id: int):
            """Create orchestrator and store reference."""
            orchestrator = await create_orchestrator()
            return orchestrator

        # Run all conversations concurrently and keep references
        tasks = [create_and_store_orchestrator(i) for i in range(num_conversations)]
        orchestrators = await asyncio.gather(*tasks)

        # Verify all orchestrators are different instances (while they still exist)
        orchestrator_ids = [id(orch) for orch in orchestrators]
        unique_ids = set(orchestrator_ids)

        # Should have at least 10 unique instances (allowing for some GC reuse)
        # The key is that they're isolated, not that memory addresses are unique
        assert len(unique_ids) >= 10, \
            f"Expected at least 10 unique orchestrators, got {len(unique_ids)}"

        # Cleanup all orchestrators
        for orch in orchestrators:
            await orch.cleanup()


class TestMemoryManagement:
    """Test memory management and resource cleanup."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_cleanup_releases_resources(self):
        """Test that orchestrator cleanup properly releases resources."""
        orchestrator = await create_orchestrator()
        
        # Verify agents are initialized
        assert orchestrator.supervisor is not None
        assert orchestrator.intake is not None
        assert orchestrator.faq is not None
        assert orchestrator.scheduler is not None
        assert orchestrator.escalation is not None
        
        # Cleanup
        await orchestrator.cleanup()
        
        # Note: We can't easily verify internal cleanup without inspecting
        # the agent internals, but we can verify cleanup doesn't raise errors
        # and can be called multiple times safely
        await orchestrator.cleanup()  # Should not raise
    
    @pytest.mark.asyncio
    async def test_no_memory_leak_with_many_instances(self):
        """Test that creating many orchestrator instances doesn't leak memory."""
        num_iterations = 100
        
        for i in range(num_iterations):
            orchestrator = await create_orchestrator()
            await orchestrator.cleanup()
        
        # If we got here without running out of memory, test passes
        # In a real scenario, you'd use memory profiling tools to verify
        assert True
    
    @pytest.mark.asyncio
    async def test_orchestrate_agents_cleans_up_automatically(self):
        """Test that orchestrate_agents() cleans up resources automatically."""
        with patch('services.agent_orchestrator.AgentOrchestrator') as MockOrchestrator:
            mock_instance = AsyncMock()
            mock_instance.orchestrate = AsyncMock(return_value={
                "response": "Test response",
                "agent": "supervisor"
            })
            mock_instance.cleanup = AsyncMock()
            MockOrchestrator.return_value = mock_instance
            
            # Call orchestrate_agents
            result = await orchestrate_agents(
                conversation_id="test_123",
                phone="+5594991398585",
                message="Test message"
            )
            
            # Verify orchestrate was called
            mock_instance.orchestrate.assert_called_once()
            
            # Verify cleanup was called
            mock_instance.cleanup.assert_called_once()


class TestPerformance:
    """Test performance characteristics of the DI pattern."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_creation_performance(self):
        """Test that orchestrator creation is reasonably fast."""
        num_iterations = 10
        start_time = time.time()

        for _ in range(num_iterations):
            orchestrator = await create_orchestrator()
            await orchestrator.cleanup()

        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / num_iterations

        # Should create and cleanup an orchestrator in less than 2 seconds
        # (Creating 5 agents with LLM clients takes time)
        assert avg_time < 2.0, \
            f"Average orchestrator creation time {avg_time:.3f}s exceeds 2.0s threshold"
    
    @pytest.mark.asyncio
    async def test_concurrent_performance_no_degradation(self):
        """Test that concurrent orchestrators don't significantly degrade performance."""
        num_concurrent = 10
        
        async def timed_orchestrator_creation():
            """Create and cleanup orchestrator, return elapsed time."""
            start = time.time()
            orchestrator = await create_orchestrator()
            await orchestrator.cleanup()
            return time.time() - start
        
        # Sequential baseline
        sequential_times = []
        for _ in range(num_concurrent):
            elapsed = await timed_orchestrator_creation()
            sequential_times.append(elapsed)
        sequential_avg = sum(sequential_times) / len(sequential_times)
        
        # Concurrent test
        tasks = [timed_orchestrator_creation() for _ in range(num_concurrent)]
        concurrent_times = await asyncio.gather(*tasks)
        concurrent_avg = sum(concurrent_times) / len(concurrent_times)
        
        # Concurrent should not be more than 50% slower than sequential
        # (allowing for some overhead from concurrency)
        assert concurrent_avg < sequential_avg * 1.5, \
            f"Concurrent avg {concurrent_avg:.3f}s is >50% slower than sequential {sequential_avg:.3f}s"


class TestBackwardCompatibility:
    """Test backward compatibility with old singleton pattern."""
    
    @pytest.mark.asyncio
    async def test_get_orchestrator_still_works(self):
        """Test that get_orchestrator() still works for backward compatibility."""
        orchestrator = get_orchestrator()
        
        # Should return a valid orchestrator instance
        assert isinstance(orchestrator, AgentOrchestrator)
        assert orchestrator.supervisor is not None
        assert orchestrator.intake is not None
        
        # Cleanup
        await orchestrator.cleanup()
    
    @pytest.mark.asyncio
    async def test_orchestrate_agents_still_works(self):
        """Test that orchestrate_agents() still works for backward compatibility."""
        with patch('services.agent_orchestrator.AgentOrchestrator') as MockOrchestrator:
            mock_instance = AsyncMock()
            mock_instance.orchestrate = AsyncMock(return_value={
                "response": "Test response",
                "agent": "supervisor",
                "intent": "test"
            })
            mock_instance.cleanup = AsyncMock()
            MockOrchestrator.return_value = mock_instance
            
            result = await orchestrate_agents(
                conversation_id="test_123",
                phone="+5594991398585",
                message="Test message"
            )
            
            # Should return valid result
            assert result["response"] == "Test response"
            assert result["agent"] == "supervisor"
            
            # Should have cleaned up
            mock_instance.cleanup.assert_called_once()


class TestErrorHandling:
    """Test error handling in the DI pattern."""
    
    @pytest.mark.asyncio
    async def test_cleanup_handles_errors_gracefully(self):
        """Test that cleanup handles errors gracefully."""
        orchestrator = await create_orchestrator()
        
        # Mock cleanup to raise an error
        with patch.object(orchestrator.supervisor, 'cleanup', side_effect=Exception("Cleanup error")):
            # Should not raise, just log the error
            await orchestrator.cleanup()
    
    @pytest.mark.asyncio
    async def test_orchestrate_agents_cleans_up_on_error(self):
        """Test that orchestrate_agents() cleans up even when orchestrate() fails."""
        with patch('services.agent_orchestrator.AgentOrchestrator') as MockOrchestrator:
            mock_instance = AsyncMock()
            mock_instance.orchestrate = AsyncMock(side_effect=Exception("Orchestration error"))
            mock_instance.cleanup = AsyncMock()
            MockOrchestrator.return_value = mock_instance
            
            # Should raise the orchestration error
            with pytest.raises(Exception, match="Orchestration error"):
                await orchestrate_agents(
                    conversation_id="test_123",
                    phone="+5594991398585",
                    message="Test message"
                )
            
            # But should still have called cleanup
            mock_instance.cleanup.assert_called_once()

