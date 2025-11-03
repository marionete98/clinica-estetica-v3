# FAQ Redis Cache Integration

## Overview

The FAQ agent cache has been migrated from in-memory storage to Redis for persistence and scalability.

## Changes Made

### 1. RedisFAQCache Class (`agents/faq.py`)

**Before:** `FAQCache` - In-memory dictionary with manual TTL management
**After:** `RedisFAQCache` - Redis-backed cache with automatic TTL

#### Key Improvements:
- **Persistence**: Cache survives application restarts
- **Shared Cache**: Multiple instances can share the same cache
- **Automatic Expiration**: Redis handles TTL natively
- **Better Scalability**: No memory limits on application side

### 2. Cache Key Structure

All FAQ cache keys use the prefix `faq_cache:` for organization:
```
faq_cache:<md5_hash_of_normalized_question>
```

### 3. Methods Updated

#### `get(question: str)`
- Uses `redis_client.get_value()` with deserialization
- Returns cached response or None
- Tracks hits/misses for metrics

#### `set(question: str, response: Dict)`
- Uses `redis_client.set_value()` with TTL
- Only caches high-confidence responses
- Automatic expiration via Redis TTL

#### `clear()`
- Deletes all `faq_cache:*` keys from Redis
- Resets hit/miss statistics


#### `get_stats()`
- Returns actual Redis key count as `current_size`
- Includes hits, misses, hit_rate, and TTL
- Queries Redis for real-time statistics

### 4. Configuration

Default settings (can be customized):
```python
faq_agent = create_faq_agent(
    llm_config,
    enable_cache=True,
    cache_ttl_seconds=3600,  # 1 hour
    cache_max_size=100       # Reference limit
)
```

## Testing

Run the integration test:
```bash
python scripts/test_faq_redis_cache.py
```

The test validates:
1. Redis connection health
2. Cache miss on first query
3. Cache hit on repeated query
4. Cache statistics accuracy
5. Question normalization
6. Cache clearing functionality

## Benefits

1. **Persistence**: Cache survives restarts and deployments
2. **Scalability**: Multiple instances share the same cache
3. **Reliability**: Redis handles expiration and memory management
4. **Observability**: Real-time cache statistics
5. **Performance**: Reduced LLM calls for common questions

## Migration Notes

- No changes required to FAQ agent API
- Backward compatible with existing code
- Uses existing `redis_client` singleton
- No additional dependencies needed

## Monitoring

Check cache performance:
```python
stats = faq_agent.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Current size: {stats['current_size']}")
```

## Rollback

To disable Redis cache:
```python
faq_agent = create_faq_agent(
    llm_config,
    enable_cache=False  # Falls back to no caching
)
```


## Files Modified

### Core Implementation
- `agents/faq.py`: Migrated `FAQCache` → `RedisFAQCache`
- `tools/kb_tools_cached.py`: Already using Redis (no changes needed)

### Tests Updated
- `tests/test_faq_cache.py`: All tests updated for Redis backend
  - Added `cache.clear()` calls for test isolation
  - Changed assertions from `len(cache._cache)` to `stats["current_size"]`
  - Updated TTL test timing for Redis behavior

### Documentation
- `docs/FAQ_REDIS_CACHE_INTEGRATION.md`: This document
- `scripts/test_faq_redis_cache.py`: Integration test script

## Validation Checklist

- [x] RedisFAQCache class implemented
- [x] Uses redis_client singleton correctly
- [x] Cache keys use `faq_cache:` prefix
- [x] TTL managed by Redis natively
- [x] get() and set() methods use redis_client
- [x] clear() deletes all FAQ cache keys
- [x] get_stats() returns actual Redis key count
- [x] All unit tests updated
- [x] Integration test script created
- [x] Documentation complete
- [x] No syntax errors

## Next Steps

1. Run unit tests: `pytest tests/test_faq_cache.py -v`
2. Run integration test: `python scripts/test_faq_redis_cache.py`
3. Monitor cache performance in production
4. Adjust TTL if needed based on usage patterns


## AutoGen RedisMemory vs RedisFAQCache

**Important Note:** AutoGen 0.4 has native `RedisMemory` support for conversation history. Our `RedisFAQCache` serves a different purpose:

- **AutoGen RedisMemory**: Stores conversation history between agents
- **RedisFAQCache**: Caches FAQ responses to reduce LLM calls

See `docs/REDIS_MEMORY_VS_FAQ_CACHE.md` for detailed comparison.

### Why We Use Custom Cache

1. **Question Normalization**: Similar questions map to same cache key
   - "Quanto custa?" → "preço"
   - "Qual o valor?" → "preço"
   
2. **Selective Caching**: Only high-confidence responses cached

3. **Cost Optimization**: Reduces LLM API calls for common questions

4. **Custom Metrics**: Hit rate, cache size, performance tracking

### Future Enhancement

Consider adding AutoGen's `RedisMemory` for conversation context:

```python
from autogen_ext.memory import RedisMemory

# Add conversation memory to FAQ agent
memory = RedisMemory(
    redis_url=settings.redis_url,
    namespace="faq_conversations"
)

faq_agent.agent.memory = memory
```

This would complement (not replace) the FAQ cache.
