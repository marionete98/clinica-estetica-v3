"""
Test orchestrator cleanup functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.agent_orchestrator import AgentOrchestrator, cleanup_orchestrator


@pytest.mark.asyncio
async def test_orchestrator_cleanup():
    """Test that orchestrator cleanup closes all agent model clients."""
    
    # Create orchestrator instance
    with patch('services.agent_orchestrator.create_supervisor_agent') as mock_supervisor, \
         patch('services.agent_orchestrator.create_intake_agent') as mock_intake, \
         patch('services.agent_orchestrator.create_faq_agent') as mock_faq, \
         patch('services.agent_orchestrator.create_scheduler_agent') as mock_scheduler, \
         patch('services.agent_orchestrator.create_escalation_agent') as mock_escalation:
        
        # Create mock agents with cleanup methods
        mock_agents = []
        for mock_create in [mock_supervisor, mock_intake, mock_faq, mock_scheduler, mock_escalation]:
            mock_agent = MagicMock()
            mock_agent.cleanup = AsyncMock()
            mock_create.return_value = mock_agent
            mock_agents.append(mock_agent)
        
        # Create orchestrator
        orchestrator = AgentOrchestrator()
        
        # Call cleanup
        await orchestrator.cleanup()
        
        # Verify all agents had cleanup called
        for mock_agent in mock_agents:
            mock_agent.cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_cleanup_handles_errors():
    """Test that orchestrator cleanup handles errors gracefully."""
    
    with patch('services.agent_orchestrator.create_supervisor_agent') as mock_supervisor, \
         patch('services.agent_orchestrator.create_intake_agent') as mock_intake, \
         patch('services.agent_orchestrator.create_faq_agent') as mock_faq, \
         patch('services.agent_orchestrator.create_scheduler_agent') as mock_scheduler, \
         patch('services.agent_orchestrator.create_escalation_agent') as mock_escalation:
        
        # Create mock agents - one will raise an error
        mock_supervisor_agent = MagicMock()
        mock_supervisor_agent.cleanup = AsyncMock(side_effect=Exception("Cleanup error"))
        mock_supervisor.return_value = mock_supervisor_agent
        
        mock_intake_agent = MagicMock()
        mock_intake_agent.cleanup = AsyncMock()
        mock_intake.return_value = mock_intake_agent
        
        # Other agents
        for mock_create in [mock_faq, mock_scheduler, mock_escalation]:
            mock_agent = MagicMock()
            mock_agent.cleanup = AsyncMock()
            mock_create.return_value = mock_agent
        
        # Create orchestrator
        orchestrator = AgentOrchestrator()
        
        # Call cleanup - should not raise exception
        await orchestrator.cleanup()
        
        # Verify supervisor cleanup was attempted (and failed)
        mock_supervisor_agent.cleanup.assert_called_once()
        
        # Verify other agents still had cleanup called
        mock_intake_agent.cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_global_cleanup_orchestrator():
    """
    Test that global cleanup_orchestrator() is a no-op with DI pattern.

    With the new dependency injection pattern, there is no global orchestrator
    instance. Each request gets its own instance that is cleaned up automatically.
    The cleanup_orchestrator() function is maintained for backward compatibility
    but does nothing.
    """
    # Call global cleanup (should be a no-op)
    await cleanup_orchestrator()

    # No assertions needed - just verify it doesn't raise an error
    # The function logs a message but doesn't perform any cleanup


@pytest.mark.asyncio
async def test_agent_cleanup_methods():
    """Test that individual agents have cleanup methods."""
    
    from agents.supervisor import SupervisorAgent
    from agents.intake import IntakeAgent
    from agents.scheduler import SchedulerAgent
    from agents.escalation import EscalationAgent
    
    # Mock LLM config
    llm_config = {
        "provider": "xai",
        "model": "grok-beta",
        "api_key": "test-key",
        "base_url": "https://api.x.ai/v1"
    }
    
    # Test each agent has cleanup method
    with patch('agents.supervisor.OpenAIChatCompletionClient'), \
         patch('agents.intake.OpenAIChatCompletionClient'), \
         patch('agents.scheduler.OpenAIChatCompletionClient'), \
         patch('agents.escalation.OpenAIChatCompletionClient'):
        
        agents = [
            SupervisorAgent(llm_config),
            IntakeAgent(llm_config),
            SchedulerAgent(llm_config),
            EscalationAgent(llm_config)
        ]
        
        for agent in agents:
            assert hasattr(agent, 'cleanup'), f"{agent.__class__.__name__} missing cleanup method"
            assert callable(agent.cleanup), f"{agent.__class__.__name__}.cleanup is not callable"
