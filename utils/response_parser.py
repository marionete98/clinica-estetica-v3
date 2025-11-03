"""
Centralized response parsing utilities for AutoGen 0.7.x agents.

This module provides robust parsing of agent responses with comprehensive
error handling and logging.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def safe_parse_response(
    response: Any,
    agent_name: str,
    fallback: Optional[str] = None
) -> str:
    """
    Parse agent response with robust error handling.
    
    Handles multiple response formats from AutoGen 0.7.x:
    - TaskResult with messages list
    - Response objects with chat_message attribute
    - Response objects with content attribute
    - Direct string responses
    - List of messages
    
    Args:
        response: Response object from agent.run() or on_messages()
        agent_name: Name of the agent (for logging context)
        fallback: Optional fallback message if parsing fails completely
    
    Returns:
        str: Extracted text content
    
    Raises:
        ValueError: If response cannot be parsed and no fallback provided
    
    Examples:
        >>> result = await agent.run(task="Hello")
        >>> text = safe_parse_response(result.messages, "faq")
        >>> print(text)
        "Hello! How can I help you?"
    """
    if response is None:
        error_msg = f"{agent_name}: Response is None"
        logger.error(error_msg)
        if fallback:
            logger.warning(f"{agent_name}: Using fallback message")
            return fallback
        raise ValueError(error_msg)
    
    try:
        # Type 1: TaskResult.messages (list of message objects)
        # This is the most common format from agent.run()
        if isinstance(response, list) and len(response) > 0:
            last_msg = response[-1]
            
            # Extract content from message object
            if hasattr(last_msg, "content"):
                content = last_msg.content
                if isinstance(content, str) and content.strip():
                    return content.strip()
                elif content:
                    # Content exists but not string - convert
                    logger.warning(
                        f"{agent_name}: Message content is {type(content)}, converting to string"
                    )
                    return str(content).strip()
                else:
                    # Empty content
                    error_msg = f"{agent_name}: Message content is empty"
                    logger.error(error_msg)
                    if fallback:
                        return fallback
                    raise ValueError(error_msg)
            
            # Fallback: convert message object to string
            msg_str = str(last_msg).strip()
            if msg_str:
                logger.warning(
                    f"{agent_name}: Message has no content attribute, using str() conversion"
                )
                return msg_str
        
        # Type 2: Response object with chat_message attribute
        if hasattr(response, "chat_message"):
            chat_msg = response.chat_message
            if hasattr(chat_msg, "content"):
                content = chat_msg.content
                if isinstance(content, str) and content.strip():
                    return content.strip()
                logger.warning(
                    f"{agent_name}: chat_message.content is {type(content)}, converting"
                )
                return str(content).strip()
        
        # Type 3: Response object with content attribute
        if hasattr(response, "content"):
            content = response.content
            if isinstance(content, str) and content.strip():
                return content.strip()
            elif content:
                logger.warning(
                    f"{agent_name}: content is {type(content)}, converting to string"
                )
                return str(content).strip()
            else:
                error_msg = f"{agent_name}: content attribute is empty"
                logger.error(error_msg)
                if fallback:
                    return fallback
                raise ValueError(error_msg)
        
        # Type 4: Direct string response
        if isinstance(response, str):
            if response.strip():
                return response.strip()
            else:
                error_msg = f"{agent_name}: Response string is empty"
                logger.error(error_msg)
                if fallback:
                    return fallback
                raise ValueError(error_msg)
        
        # Type 5: Empty list
        if isinstance(response, list) and len(response) == 0:
            error_msg = f"{agent_name}: Response is empty list"
            logger.error(error_msg)
            if fallback:
                return fallback
            raise ValueError(error_msg)
        
        # Last resort: convert to string
        response_str = str(response).strip()
        if response_str and response_str != "None":
            logger.warning(
                f"{agent_name}: Unknown response type {type(response)}, "
                f"using str() conversion: {response_str[:100]}"
            )
            return response_str
        
        # Complete failure
        error_msg = (
            f"{agent_name}: Unable to parse response of type {type(response)}. "
            f"Response: {str(response)[:200]}"
        )
        logger.error(error_msg)
        if fallback:
            logger.warning(f"{agent_name}: Using fallback message after parse failure")
            return fallback
        raise ValueError(error_msg)
    
    except ValueError:
        # Re-raise ValueError (already logged)
        raise
    except Exception as e:
        error_msg = f"{agent_name}: Unexpected error parsing response: {e}"
        logger.error(error_msg, exc_info=True)
        if fallback:
            logger.warning(f"{agent_name}: Using fallback message after exception")
            return fallback
        raise ValueError(error_msg) from e


def parse_messages_from_run_result(run_result: Any, agent_name: str) -> str:
    """
    Convenience function to parse TaskResult from agent.run().
    
    Args:
        run_result: TaskResult object from agent.run()
        agent_name: Name of the agent (for logging)
    
    Returns:
        str: Extracted text content
    
    Raises:
        ValueError: If response cannot be parsed
    
    Examples:
        >>> run_result = await agent.run(task="Hello")
        >>> text = parse_messages_from_run_result(run_result, "faq")
    """
    if hasattr(run_result, "messages"):
        return safe_parse_response(run_result.messages, agent_name)
    else:
        # Fallback: treat entire result as response
        logger.warning(
            f"{agent_name}: run_result has no messages attribute, "
            f"parsing entire result"
        )
        return safe_parse_response(run_result, agent_name)

