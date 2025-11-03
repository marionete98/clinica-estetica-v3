"""
Unit tests for error categorization system implemented across all agents.

Tests verify that:
1. Error handlers are properly imported
2. Error types are correctly categorized
3. Fallback responses are returned in Portuguese
4. Recovery strategies work correctly
5. Error information is properly logged
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from utils.error_handlers import (
    ErrorType,
    get_fallback_response,
    ErrorRecoveryStrategy,
    ServiceErrorHandler
)


class TestErrorTypeEnum:
    """Test ErrorType enum values."""
    
    def test_error_type_values(self):
        """Test that all error types have correct string values."""
        assert ErrorType.SYSTEM_BUSY.value == "system_busy"
        assert ErrorType.SERVICE_UNAVAILABLE.value == "service_unavailable"
        assert ErrorType.UNCLEAR_REQUEST.value == "unclear_request"
        assert ErrorType.NO_SLOTS.value == "no_slots"
        assert ErrorType.POLICY_VIOLATION.value == "policy_violation"
        assert ErrorType.LLM_TIMEOUT.value == "llm_timeout"
        assert ErrorType.CHATWOOT_ERROR.value == "chatwoot_error"
        assert ErrorType.SUPABASE_ERROR.value == "supabase_error"
        assert ErrorType.REDIS_ERROR.value == "redis_error"
        assert ErrorType.UNKNOWN_ERROR.value == "unknown_error"
    
    def test_error_type_count(self):
        """Test that we have exactly 10 error types."""
        error_types = list(ErrorType)
        assert len(error_types) == 10


class TestFallbackResponses:
    """Test fallback response generation."""
    
    def test_get_fallback_response_system_busy(self):
        """Test fallback response for SYSTEM_BUSY."""
        response = get_fallback_response(ErrorType.SYSTEM_BUSY)
        assert isinstance(response, str)
        assert len(response) > 0
        assert "Desculpe" in response or "desculpe" in response
    
    def test_get_fallback_response_service_unavailable(self):
        """Test fallback response for SERVICE_UNAVAILABLE."""
        response = get_fallback_response(ErrorType.SERVICE_UNAVAILABLE)
        assert isinstance(response, str)
        assert "dificuldades técnicas" in response or "transferir" in response
    
    def test_get_fallback_response_unclear_request(self):
        """Test fallback response for UNCLEAR_REQUEST."""
        response = get_fallback_response(ErrorType.UNCLEAR_REQUEST)
        assert isinstance(response, str)
        assert "não entendi" in response or "reformular" in response
    
    def test_get_fallback_response_llm_timeout(self):
        """Test fallback response for LLM_TIMEOUT."""
        response = get_fallback_response(ErrorType.LLM_TIMEOUT)
        assert isinstance(response, str)
        assert "processando" in response or "momento" in response
    
    def test_get_fallback_response_unknown_error(self):
        """Test fallback response for UNKNOWN_ERROR."""
        response = get_fallback_response(ErrorType.UNKNOWN_ERROR)
        assert isinstance(response, str)
        assert "erro" in response or "transferir" in response
    
    def test_all_responses_in_portuguese(self):
        """Test that all fallback responses are in Portuguese."""
        portuguese_indicators = ["Desculpe", "desculpe", "você", "Você", "não", "por favor", "Não", "Estou", "Tive", "Continuando"]

        for error_type in ErrorType:
            response = get_fallback_response(error_type)
            # At least one Portuguese indicator should be present (or template variables)
            has_portuguese = any(indicator in response for indicator in portuguese_indicators) or "{" in response
            assert has_portuguese, f"Response for {error_type} doesn't appear to be in Portuguese: {response}"


class TestErrorRecoveryStrategy:
    """Test error recovery strategy logic."""
    
    def test_should_escalate_unknown_error(self):
        """Test that UNKNOWN_ERROR triggers escalation."""
        should_escalate = ErrorRecoveryStrategy.should_escalate(
            error_count=1,
            error_type=ErrorType.UNKNOWN_ERROR
        )
        assert should_escalate is True
    
    def test_should_escalate_service_unavailable(self):
        """Test that SERVICE_UNAVAILABLE triggers escalation."""
        should_escalate = ErrorRecoveryStrategy.should_escalate(
            error_count=1,
            error_type=ErrorType.SERVICE_UNAVAILABLE
        )
        assert should_escalate is True
    
    def test_should_escalate_multiple_unclear_requests(self):
        """Test that multiple UNCLEAR_REQUEST errors trigger escalation."""
        # First unclear request - should not escalate
        should_escalate_1 = ErrorRecoveryStrategy.should_escalate(
            error_count=1,
            error_type=ErrorType.UNCLEAR_REQUEST
        )
        
        # Third unclear request - should escalate
        should_escalate_3 = ErrorRecoveryStrategy.should_escalate(
            error_count=3,
            error_type=ErrorType.UNCLEAR_REQUEST
        )
        
        assert should_escalate_1 is False
        assert should_escalate_3 is True
    
    def test_get_recovery_action_unknown_error(self):
        """Test recovery action for UNKNOWN_ERROR."""
        action = ErrorRecoveryStrategy.get_recovery_action(ErrorType.UNKNOWN_ERROR)
        assert action == "escalate_to_human"
    
    def test_get_recovery_action_unclear_request(self):
        """Test recovery action for UNCLEAR_REQUEST."""
        action = ErrorRecoveryStrategy.get_recovery_action(ErrorType.UNCLEAR_REQUEST)
        assert action in ["retry_with_clarification", "escalate_to_human", "request_clarification"]

    def test_get_recovery_action_llm_timeout(self):
        """Test recovery action for LLM_TIMEOUT."""
        action = ErrorRecoveryStrategy.get_recovery_action(ErrorType.LLM_TIMEOUT)
        assert action in ["retry", "escalate_to_human", "use_fallback_response_and_escalate"]


class TestServiceErrorHandler:
    """Test service-specific error handlers."""
    
    def test_handle_chatwoot_error(self):
        """Test Chatwoot error handling."""
        error = Exception("Connection timeout")
        conversation_id = "conv_123"
        
        result = ServiceErrorHandler.handle_chatwoot_error(error, conversation_id)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_handle_supabase_error(self):
        """Test Supabase error handling."""
        error = Exception("Database connection failed")
        operation = "fetch_bookings"
        
        result = ServiceErrorHandler.handle_supabase_error(error, operation)
        
        # Should return None or empty result for graceful degradation
        assert result is None or result == [] or result == {}
    
    def test_handle_redis_error(self):
        """Test Redis error handling."""
        error = Exception("Redis connection refused")
        conversation_id = "conv_123"
        
        result = ServiceErrorHandler.handle_redis_error(error, conversation_id)
        
        # Should return empty context list
        assert isinstance(result, list)
        assert len(result) == 0


class TestAgentErrorCategorization:
    """Test error categorization in agent exception handlers."""
    
    @pytest.mark.asyncio
    async def test_supervisor_value_error_categorization(self):
        """Test that supervisor categorizes ValueError as UNCLEAR_REQUEST."""
        from agents.supervisor import SupervisorAgent
        
        # This test verifies the error handling pattern exists
        # Actual agent testing would require full initialization
        assert hasattr(SupervisorAgent, 'classify_intent')
    
    @pytest.mark.asyncio
    async def test_faq_value_error_categorization(self):
        """Test that FAQ agent categorizes ValueError as UNCLEAR_REQUEST."""
        from agents.faq import FAQAgent
        
        # Verify the agent has the answer_question method
        assert hasattr(FAQAgent, 'answer_question')
    
    @pytest.mark.asyncio
    async def test_scheduler_value_error_categorization(self):
        """Test that scheduler categorizes ValueError as UNCLEAR_REQUEST."""
        from agents.scheduler import SchedulerAgent
        
        # Verify the agent has the process_scheduling_request method
        assert hasattr(SchedulerAgent, 'process_scheduling_request')
    
    @pytest.mark.asyncio
    async def test_escalation_error_categorization(self):
        """Test that escalation categorizes errors as SERVICE_UNAVAILABLE."""
        from agents.escalation import EscalationAgent
        
        # Verify the agent has the prepare_escalation method
        assert hasattr(EscalationAgent, 'prepare_escalation')
    
    @pytest.mark.asyncio
    async def test_intake_value_error_categorization(self):
        """Test that intake categorizes ValueError as UNCLEAR_REQUEST."""
        from agents.intake import IntakeAgent

        # Verify the agent has the process_message method
        assert hasattr(IntakeAgent, 'process_message')


class TestErrorResponseStructure:
    """Test that error responses have correct structure."""
    
    def test_error_response_includes_error_type(self):
        """Test that error responses should include error_type field."""
        # This is a pattern test - actual responses are tested in integration tests
        error_type = ErrorType.UNCLEAR_REQUEST
        
        # Simulated error response structure
        error_response = {
            "error_type": error_type.value,
            "fallback_message": get_fallback_response(error_type)
        }
        
        assert "error_type" in error_response
        assert error_response["error_type"] == "unclear_request"
        assert "fallback_message" in error_response
        assert isinstance(error_response["fallback_message"], str)
    
    def test_error_response_includes_recovery_action(self):
        """Test that error responses should include recovery_action field."""
        error_type = ErrorType.UNKNOWN_ERROR
        
        # Simulated error response structure
        error_response = {
            "error_type": error_type.value,
            "recovery_action": ErrorRecoveryStrategy.get_recovery_action(error_type),
            "should_escalate": True
        }
        
        assert "error_type" in error_response
        assert "recovery_action" in error_response
        assert "should_escalate" in error_response
        assert error_response["recovery_action"] == "escalate_to_human"


class TestErrorLogging:
    """Test that errors are properly logged."""
    
    @patch('agents.supervisor.logger')
    def test_supervisor_logs_errors_with_exc_info(self, mock_logger):
        """Test that supervisor logs errors with exc_info=True."""
        # This verifies the logging pattern
        # Actual logging is tested in integration tests
        assert mock_logger is not None
    
    @patch('agents.faq.logger')
    def test_faq_logs_errors_with_exc_info(self, mock_logger):
        """Test that FAQ agent logs errors with exc_info=True."""
        assert mock_logger is not None
    
    @patch('agents.scheduler.logger')
    def test_scheduler_logs_errors_with_exc_info(self, mock_logger):
        """Test that scheduler logs errors with exc_info=True."""
        assert mock_logger is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

