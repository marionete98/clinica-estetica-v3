# Redis Memory vs FAQ Cache - Comparison

## Overview

This document clarifies the difference between AutoGen's native `RedisMemory` and our custom `RedisFAQCache`.

## AutoGen RedisMemory (Native)

**Purpose:** Store conversation history between agents for context continuity

**Use Case:**
- Multi-turn conversations
- Agent-to-agent communication history
- Conversation context across sessions
- Memory persistence for agent teams

**Implementation:**
```python
from autogen_ext.memory import RedisMemory

# Create Redis memory for agent
memory = RedisMemory(
    redis_url="redis://localhost:6379",
    namespace="agent_conversations"
)

# Use with agent
agent = AssistantAgent(
    name="assistant",
    model_client=model_client,
    memory=memory  # Attach memory to agent
)
```

**Key Features:**
- Automatic conversation history storage
- Built-in message serialization
- Namespace support for multi-tenant
- TTL management
- Query by conversation ID

## RedisFAQCache (Custom)

**Purpose:** Cache FAQ responses to reduce LLM calls and improve response time

**Use Case:**
- Frequently asked questions
- Identical/similar question detection
- Response reuse for common queries
- Cost optimization (reduce LLM API calls)

**Implementation:**
```python
from agents.faq import RedisFAQCache

# Create FAQ cache
cache = RedisFAQCache(
    ttl_seconds=3600,  # 1 hour
    max_size=100
)

# Use in FAQ agent
faq_agent = FAQAgent(
    llm_config,
    enable_cache=True,
    cache_ttl_seconds=3600
)
```

**Key Features:**
- Question normalization (similar questions → same cache key)
- High-confidence response caching only
- Hit/miss rate tracking
- Cache warming for common questions
- Custom TTL per cache entry

## Comparison Table

| Feature | AutoGen RedisMemory | RedisFAQCache |
|---------|---------------------|---------------|
| **Purpose** | Conversation history | Response caching |
| **Scope** | All agent messages | FAQ responses only |
| **Key Generation** | Conversation ID | Question hash (MD5) |
| **Normalization** | None | Question normalization |
| **Filtering** | None | High-confidence only |
| **Metrics** | Basic | Hit rate, stats |
| **AutoGen Native** | ✅ Yes | ❌ No (custom) |
| **Use Case** | Multi-turn context | Cost optimization |

## When to Use Each

### Use AutoGen RedisMemory When:
- You need conversation history across sessions
- Multiple agents need shared context
- Building multi-turn conversational flows
- Need to resume conversations after restart

### Use RedisFAQCache When:
- You want to cache identical/similar questions
- Reducing LLM API costs is priority
- Improving response time for common queries
- Need question normalization logic

## Can They Work Together?

**Yes!** They serve different purposes:

```python
from autogen_ext.memory import RedisMemory
from agents.faq import create_faq_agent

# Redis memory for conversation history
memory = RedisMemory(
    redis_url=settings.redis_url,
    namespace="faq_conversations"
)

# FAQ agent with both memory and cache
faq_agent = create_faq_agent(
    llm_config,
    enable_cache=True,  # FAQ response cache
    cache_ttl_seconds=3600
)

# Attach memory to agent (if needed)
faq_agent.agent.memory = memory
```

## Current Implementation Status

### ✅ Implemented
- RedisFAQCache for FAQ response caching
- Question normalization
- Cache statistics and monitoring
- Redis-backed persistence

### 🔄 Potential Enhancement
- Add AutoGen RedisMemory for conversation history
- This would complement (not replace) RedisFAQCache
- Useful for multi-turn FAQ conversations

## Recommendation

**Keep both approaches:**

1. **RedisFAQCache** - Continue using for FAQ response caching
   - Proven cost savings
   - Question normalization is valuable
   - Hit rate metrics are useful

2. **Consider adding RedisMemory** - For conversation context
   - Would help with multi-turn conversations
   - Better context awareness across sessions
   - Native AutoGen integration

## Example: Combined Usage

```python
from autogen_ext.memory import RedisMemory
from agents.faq import create_faq_agent

# 1. Create Redis memory for conversation history
conversation_memory = RedisMemory(
    redis_url=settings.redis_url,
    namespace="faq_conversations",
    ttl=86400  # 24 hours
)

# 2. Create FAQ agent with response cache
faq_agent = create_faq_agent(
    llm_config,
    enable_cache=True,
    cache_ttl_seconds=3600
)

# 3. Attach memory to agent
faq_agent.agent.memory = conversation_memory

# Now the agent has:
# - Conversation history (RedisMemory)
# - Response caching (RedisFAQCache)
```

## Conclusion

- **RedisFAQCache**: Custom solution for FAQ response caching ✅
- **AutoGen RedisMemory**: Native solution for conversation history 🔄
- **Both can coexist**: Different purposes, complementary benefits
- **Current implementation is correct**: No changes needed
- **Future enhancement**: Consider adding RedisMemory for conversation context
