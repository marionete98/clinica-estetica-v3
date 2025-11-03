"""
Example demonstrating integrated error handling, graceful degradation, and validation.
This shows how to use all three modules together in a real webhook processing scenario.
"""

import asyncio
from typing import Optional
import structlog

from utils.validators import (
    validate_and_sanitize_webhook,
    InputSanitizer,
    ValidationResult
)
from utils.error_handlers import (
    ErrorType,
    get_fallback_response,
    retry_chatwoot,
    LLMTimeoutHandler,
    ServiceErrorHandler
)
from utils.graceful_degradation import (
    degradation_manager,
    degradation_strategy,
    ServiceStatus,
    DegradationMode
)

logger = structlog.get_logger(__name__)


class WebhookProcessor:
    """Example webhook processor with full error handling."""
    
    def __init__(self):
        """Initialize processor."""
        self.error_counts = {}  # Track errors per conversation
    
    async def process_webhook(self, payload: dict) -> tuple[int, dict]:
        """
        Process incoming webhook with validation and error handling.
        
        Args:
            payload: Raw webhook payload
        
        Returns:
            tuple: (status_code, response_dict)
        """
        # Step 1: Validate and sanitize webhook payload
        validation_result = validate_and_sanitize_webhook(payload)
        
        if not validation_result.is_valid:
            logger.error(
                "webhook_validation_failed",
                error=validation_result.error
            )
            return 400, {"error": validation_result.error}
        
        validated = validation_result.data
        conversation_id = str(validated.get_conversation_id())
        
        # Step 2: Check system degradation mode
        degradation_mode = degradation_manager.get_degradation_mode()
        
        if degradation_mode == DegradationMode.ESCALATION_ONLY:
            logger.warning(
                "system_degraded_escalating",
                conversation_id=conversation_id,
                mode=degradation_mode
            )
            
            response = get_fallback_response(ErrorType.SERVICE_UNAVAILABLE)
            await self._send_message_safe(conversation_id, response)
            await self._escalate_to_human(conversation_id)
            
            return 200, {"status": "escalated", "reason": "system_degraded"}
        
        # Step 3: Get conversation context (with degradation handling)
        context = await self._get_context_safe(conversation_id)
        
        # Step 4: Sanitize message for LLM
        user_message = validated.content
        sanitized_message = InputSanitizer.sanitize_for_llm(user_message)
        
        # Step 5: Process message with error handling
        try:
            response = await self._process_message_with_llm(
                conversation_id=conversation_id,
                message=sanitized_message,
                context=context
            )
            
            # Step 6: Send response
            await self._send_message_safe(conversation_id, response)
            
            # Step 7: Update context (skip if Redis is down)
            await self._update_context_safe(conversation_id, user_message, response)
            
            # Reset error count on success
            self.error_counts[conversation_id] = 0
            
            return 200, {"status": "ok"}
        
        except Exception as e:
            logger.error(
                "message_processing_failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            
            # Track errors
            self.error_counts[conversation_id] = self.error_counts.get(conversation_id, 0) + 1
            
            # Check if should escalate
            if self.error_counts[conversation_id] >= 3:
                logger.warning(
                    "escalating_after_errors",
                    conversation_id=conversation_id,
                    error_count=self.error_counts[conversation_id]
                )
                
                response = get_fallback_response(ErrorType.SERVICE_UNAVAILABLE)
                await self._send_message_safe(conversation_id, response)
                await self._escalate_to_human(conversation_id)
                
                return 200, {"status": "escalated", "reason": "repeated_errors"}
            
            # Send generic error response
            response = get_fallback_response(ErrorType.SYSTEM_BUSY)
            await self._send_message_safe(conversation_id, response)
            
            return 500, {"status": "error", "message": str(e)}
    
    async def _get_context_safe(self, conversation_id: str) -> list:
        """
        Get conversation context with graceful degradation.
        
        Args:
            conversation_id: Conversation identifier
        
        Returns:
            list: Context messages (empty if Redis is down)
        """
        # Check if should skip context retrieval
        if degradation_strategy.should_skip_operation("context_update"):
            logger.info(
                "context_retrieval_skipped",
                conversation_id=conversation_id,
                reason="redis_unavailable"
            )
            return []
        
        try:
            # Simulate Redis context retrieval
            from config.redis_client import redis_client
            context = redis_client.get_context(conversation_id)
            return context
        
        except Exception as e:
            # Handle Redis error gracefully
            logger.warning(
                "context_retrieval_failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            
            # Update service status
            degradation_manager.update_service_status("redis", ServiceStatus.UNAVAILABLE)
            
            # Return empty context
            return []
    
    async def _process_message_with_llm(
        self,
        conversation_id: str,
        message: str,
        context: list
    ) -> str:
        """
        Process message with LLM including timeout handling.
        
        Args:
            conversation_id: Conversation identifier
            message: Sanitized user message
            context: Conversation context
        
        Returns:
            str: LLM response or fallback
        """
        # Check if should use LLM or fallback
        use_llm, fallback_response = degradation_strategy.get_response_strategy("faq")
        
        if not use_llm:
            logger.info(
                "using_fallback_response",
                conversation_id=conversation_id,
                reason="llm_unavailable"
            )
            return fallback_response
        
        # Get timeout for current provider
        from config.settings import settings
        provider = settings.model_provider
        timeout = LLMTimeoutHandler.get_timeout(provider)
        
        try:
            # Simulate LLM call with timeout
            response = await asyncio.wait_for(
                self._call_llm(message, context),
                timeout=timeout
            )
            
            return response
        
        except asyncio.TimeoutError:
            logger.error(
                "llm_timeout",
                conversation_id=conversation_id,
                provider=provider,
                timeout=timeout
            )
            
            # Update service status
            degradation_manager.update_service_status("llm", ServiceStatus.DEGRADED)
            
            # Get timeout fallback
            fallback = LLMTimeoutHandler.handle_timeout(provider, conversation_id)
            
            # Escalate conversation
            await self._escalate_to_human(conversation_id)
            
            return fallback
    
    async def _call_llm(self, message: str, context: list) -> str:
        """
        Simulate LLM call.
        
        Args:
            message: User message
            context: Conversation context
        
        Returns:
            str: LLM response
        """
        # This would be replaced with actual LLM call
        await asyncio.sleep(0.1)
        return "Esta é uma resposta simulada do LLM."
    
    @retry_chatwoot
    async def _send_message_safe(self, conversation_id: str, message: str) -> bool:
        """
        Send message with retry logic.
        
        Args:
            conversation_id: Conversation identifier
            message: Message to send
        
        Returns:
            bool: True if successful
        """
        try:
            # Simulate Chatwoot API call
            from config.chatwoot_client import chatwoot_client
            result = chatwoot_client.send_message(
                conversation_id=int(conversation_id),
                content=message
            )
            
            if result:
                logger.info(
                    "message_sent",
                    conversation_id=conversation_id
                )
                return True
            
            return False
        
        except Exception as e:
            logger.error(
                "message_send_failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            
            # Update service status
            degradation_manager.update_service_status("chatwoot", ServiceStatus.DEGRADED)
            
            raise
    
    async def _update_context_safe(
        self,
        conversation_id: str,
        user_message: str,
        assistant_message: str
    ) -> bool:
        """
        Update conversation context with graceful degradation.
        
        Args:
            conversation_id: Conversation identifier
            user_message: User's message
            assistant_message: Assistant's response
        
        Returns:
            bool: True if successful or skipped
        """
        # Check if should skip context update
        if degradation_strategy.should_skip_operation("context_update"):
            logger.debug(
                "context_update_skipped",
                conversation_id=conversation_id
            )
            return True
        
        try:
            from config.redis_client import redis_client
            
            # Add user message
            redis_client.append_message(
                conversation_id=conversation_id,
                role="user",
                content=user_message
            )
            
            # Add assistant message
            redis_client.append_message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_message
            )
            
            return True
        
        except Exception as e:
            logger.warning(
                "context_update_failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            
            # Don't fail the request if context update fails
            return True
    
    async def _escalate_to_human(self, conversation_id: str) -> bool:
        """
        Escalate conversation to human agent.
        
        Args:
            conversation_id: Conversation identifier
        
        Returns:
            bool: True if successful
        """
        try:
            from config.chatwoot_client import chatwoot_client
            
            # Assign to human
            success = chatwoot_client.assign_conversation(
                conversation_id=int(conversation_id)
            )
            
            if success:
                logger.info(
                    "conversation_escalated",
                    conversation_id=conversation_id
                )
            
            return success
        
        except Exception as e:
            logger.error(
                "escalation_failed",
                conversation_id=conversation_id,
                error=str(e)
            )
            return False


# Example usage
async def main():
    """Example main function."""
    processor = WebhookProcessor()
    
    # Example webhook payload
    webhook_payload = {
        "event": "message_created",
        "message_type": "incoming",
        "content": "Olá, gostaria de agendar uma consulta",
        "conversation": {
            "id": 12345
        },
        "sender": {
            "phone_number": "(94) 99139-8585",
            "name": "João Silva"
        },
        "account": {
            "id": 1
        }
    }
    
    # Process webhook
    status_code, response = await processor.process_webhook(webhook_payload)
    
    print(f"Status: {status_code}")
    print(f"Response: {response}")
    
    # Simulate Redis failure
    print("\n--- Simulating Redis failure ---")
    degradation_manager.update_service_status("redis", ServiceStatus.UNAVAILABLE)
    
    status_code, response = await processor.process_webhook(webhook_payload)
    print(f"Status: {status_code}")
    print(f"Response: {response}")
    print(f"Degradation mode: {degradation_manager.get_degradation_mode()}")


if __name__ == "__main__":
    # Run example
    asyncio.run(main())
