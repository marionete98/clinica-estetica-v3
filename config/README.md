# Configuration Module

This directory contains the configuration and client modules for external service connections.

## Modules

### 1. `settings.py`
Configuration management using pydantic-settings.

**Features:**
- Loads environment variables from `.env` file
- Validates required configuration based on selected LLM provider
- Provides typed access to all application settings
- Supports switching between xAI Grok and Google Gemini providers

**Usage:**
```python
from config.settings import settings

# Get LLM configuration
llm_config = settings.get_llm_config()

# Check environment
if settings.is_production:
    # Production logic
    pass
```

### 2. `supabase_client.py`
Supabase database client with connection pooling and retry logic.

**Features:**
- Automatic connection initialization with service role key
- Retry logic for read/write operations (3 attempts with exponential backoff)
- High-level operations wrapper (select, insert, update, delete, rpc)
- Health check functionality

**Usage:**
```python
from config.supabase_client import supabase_ops

# Select data
contacts = supabase_ops.select(
    table="contacts",
    filters={"phone": "+5594991398585"},
    limit=1
)

# Insert data
new_contact = supabase_ops.insert(
    table="contacts",
    data={"phone": "+5594991398585", "name": "João Silva"}
)
```

### 3. `redis_client.py`
Redis client for conversation context management with TTL and locking.

**Features:**
- Conversation context storage with 24-hour TTL
- Automatic trimming to last 20 messages
- Lock mechanism to prevent concurrent processing
- Graceful degradation on connection failures

**Usage:**
```python
from config.redis_client import redis_client

# Get conversation context
messages = redis_client.get_context("conv_12345")

# Append message
redis_client.append_message(
    conversation_id="conv_12345",
    role="user",
    content="Quero agendar uma consulta"
)

# Use lock to prevent concurrent processing
with redis_client.acquire_lock("conv_12345"):
    # Process conversation
    pass
```

### 4. `chatwoot_client.py`
Chatwoot API client for message sending and conversation management.

**Features:**
- Message sending with retry logic (3 attempts with exponential backoff)
- Rate limiting (100 requests/minute)
- Webhook signature validation
- Conversation assignment to human agents
- Status management and labeling

**Usage:**
```python
from config.chatwoot_client import chatwoot_client

# Send message
chatwoot_client.send_message(
    conversation_id=12345,
    content="Seu agendamento foi confirmado!"
)

# Validate webhook
is_valid = chatwoot_client.validate_webhook_signature(
    payload=request.body,
    signature=request.headers.get("X-Chatwoot-Signature")
)

# Assign to human agent
chatwoot_client.assign_conversation(
    conversation_id=12345,
    assignee_id=67890
)
```

## Environment Variables

All required environment variables are documented in `.env.example`. Key variables:

- `MODEL_PROVIDER`: LLM provider selection ('xai' or 'gemini')
- `XAI_API_KEY`: xAI API key (required if MODEL_PROVIDER=xai)
- `GEMINI_API_KEY`: Google Gemini API key (required if MODEL_PROVIDER=gemini)
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase service role key
- `REDIS_URL`: Redis connection URL
- `CHATWOOT_API_URL`: Chatwoot API base URL
- `CHATWOOT_ACCOUNT_ID`: Chatwoot account ID
- `CHATWOOT_API_TOKEN`: Chatwoot API access token
- `CHATWOOT_WEBHOOK_SECRET`: Chatwoot webhook secret for signature validation

## Error Handling

All clients implement robust error handling:

- **Retry Logic**: Automatic retries with exponential backoff for transient failures
- **Graceful Degradation**: Redis client returns empty context on failure
- **Structured Logging**: All operations logged with structlog for observability
- **Health Checks**: Each client provides health check functionality

## Testing

Run tests with:
```bash
pytest tests/test_config.py -v
```

## Requirements

See `requirements.txt` for all dependencies. Key packages:
- `pydantic-settings`: Configuration management
- `supabase`: Supabase client
- `redis`: Redis client
- `httpx`: HTTP client for Chatwoot API
- `structlog`: Structured logging
