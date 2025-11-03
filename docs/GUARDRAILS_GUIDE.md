# LLM Guardrails Guide

## Overview

The guardrails system provides safety limits and controls for LLM interactions to prevent abuse, control costs, and protect against prompt injection attacks.

## Features

### 1. Tool Call Limiting
- **Limit**: Maximum 3 tool calls per agent session
- **Purpose**: Prevents infinite loops and excessive API calls
- **Scope**: Per conversation + session ID

### 2. Response Token Limiting
- **Limit**: Maximum 500 tokens per response
- **Purpose**: Controls response length and costs
- **Scope**: Per individual response

### 3. Conversation Token Limiting
- **Limit**: Maximum 10,000 tokens per conversation per hour
- **Purpose**: Prevents runaway costs from long conversations
- **Scope**: Per conversation ID, rolling 1-hour window

### 4. User Message Sanitization
- **Feature**: Adds "User says:" prefix to all user messages
- **Purpose**: Prevents prompt injection attacks
- **Implementation**: Clearly separates user input from system instructions

## Usage

### Basic Usage

```python
from utils.guardrails import guardrails, GuardrailViolation

# Check and increment tool calls
try:
    guardrails.check_tool_call_limit(conversation_id, session_id)
    # ... execute tool call ...
    guardrails.increment_tool_call_count(conversation_id, session_id)
except GuardrailViolation as e:
    logger.warning(f"Guardrail violated: {e.message}")
    # Handle violation (e.g., escalate to human)
```

### Helper Functions

```python
from utils.guardrails import (
    check_and_increment_tool_calls,
    check_and_increment_tokens,
    estimate_tokens
)

# Check and increment in one operation
try:
    count = check_and_increment_tool_calls(conversation_id, session_id)
    logger.info(f"Tool call count: {count}")
except GuardrailViolation:
    # Handle violation
    pass

# Estimate tokens for text
text = "Hello, I want to book an appointment"
tokens = estimate_tokens(text)
```

### Message Sanitization

```python
from utils.guardrails import guardrails

# Sanitize user input before passing to LLM
user_message = "I want to book an appointment"
sanitized = guardrails.sanitize_user_message(user_message)
# Result: "User says: I want to book an appointment"
```

### Checking Current Limits

```python
# Get current counts without incrementing
tool_calls = guardrails.get_tool_call_count(conversation_id, session_id)
tokens = guardrails.get_conversation_token_count(conversation_id)

logger.info(f"Tool calls: {tool_calls}/3")
logger.info(f"Tokens this hour: {tokens}/10000")
```

### Resetting Limits (Testing/Admin)

```python
# Reset session limits (useful for testing)
guardrails.reset_session_limits(conversation_id, session_id)
```

## Integration with Agent Orchestrator

The guardrails should be integrated into the agent orchestration flow:

```python
from utils.guardrails import guardrails, GuardrailViolation, estimate_tokens

async def process_conversation(conversation_id: str, message: str):
    session_id = generate_session_id()
    
    # Sanitize user input
    sanitized_message = guardrails.sanitize_user_message(message)
    
    # Check token limits
    estimated_tokens = estimate_tokens(sanitized_message)
    try:
        guardrails.check_conversation_token_limit(conversation_id, estimated_tokens)
    except GuardrailViolation as e:
        logger.warning(f"Token limit exceeded: {e}")
        return "Você atingiu o limite de mensagens por hora. Por favor, tente novamente mais tarde."
    
    # Process with agents
    try:
        # Before each tool call
        guardrails.check_tool_call_limit(conversation_id, session_id)
        
        # Execute tool
        result = execute_tool(...)
        
        # After successful tool call
        guardrails.increment_tool_call_count(conversation_id, session_id)
        
    except GuardrailViolation as e:
        logger.warning(f"Tool call limit exceeded: {e}")
        # Escalate to human
        return escalate_to_human(conversation_id)
    
    # Check response token limit
    response_tokens = estimate_tokens(response)
    try:
        guardrails.check_response_token_limit(response_tokens)
    except GuardrailViolation:
        # Truncate response or use shorter template
        response = get_short_response_template()
    
    # Increment conversation tokens
    total_tokens = estimated_tokens + response_tokens
    guardrails.increment_conversation_tokens(conversation_id, total_tokens)
    
    return response
```

## Error Handling

### GuardrailViolation Exception

```python
try:
    guardrails.check_tool_call_limit(conversation_id, session_id)
except GuardrailViolation as e:
    # Access violation details
    print(f"Limit type: {e.limit_type}")
    print(f"Current value: {e.current_value}")
    print(f"Max value: {e.max_value}")
    print(f"Message: {e.message}")
```

### Fail-Open Strategy

The guardrails system uses a "fail-open" strategy for Redis errors:
- If Redis is unavailable, limits are not enforced
- System continues operating (graceful degradation)
- Errors are logged for monitoring

## Configuration

Guardrail limits are configured in `config/settings.py`:

```python
# Agent Configuration
max_tool_calls_per_session: int = 3
response_timeout_seconds: int = 10
max_context_messages: int = 20
```

Token limits are hardcoded in `utils/guardrails.py`:
- `max_tokens_per_response = 500`
- `max_tokens_per_conversation_hour = 10000`

## Monitoring

Monitor guardrail violations in logs:

```python
# Logs include structured data
logger.warning(
    "tool_call_limit_exceeded",
    conversation_id=conversation_id,
    session_id=session_id,
    current_count=count,
    max_allowed=max_allowed
)
```

Query violations from Supabase logs table:

```sql
SELECT 
    ts,
    conversation_id,
    intent,
    error_message
FROM logs
WHERE error_message LIKE '%limit exceeded%'
ORDER BY ts DESC
LIMIT 100;
```

## Best Practices

1. **Always sanitize user input** before passing to LLM
2. **Check limits before expensive operations** (tool calls, LLM requests)
3. **Increment counters after successful operations** to avoid double-counting on retries
4. **Handle GuardrailViolation gracefully** with user-friendly messages
5. **Monitor violation rates** to adjust limits if needed
6. **Use helper functions** for common patterns (check + increment)
7. **Log all violations** for analysis and optimization

## Testing

Run guardrails tests:

```bash
pytest tests/test_guardrails.py -v
```

Test coverage includes:
- Tool call limiting
- Token limiting (response and conversation)
- Message sanitization
- Counter operations
- Error handling
- Helper functions

## Rate Limiting vs Guardrails

**Rate Limiting** (`middleware/rate_limit.py`):
- Limits requests per minute per conversation
- Protects against DoS attacks
- Applied at HTTP middleware level
- Returns 429 status code

**Guardrails** (`utils/guardrails.py`):
- Limits LLM operations within a request
- Protects against cost overruns
- Applied at application logic level
- Raises GuardrailViolation exception

Both systems work together to provide comprehensive protection.
