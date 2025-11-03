# Message Deduplication and Batching

## Overview

The webhook endpoint implements message deduplication and batching mechanisms to handle duplicate messages from Chatwoot and batch rapid-fire messages from users.

**Implementation Date:** October 16, 2025  
**File:** `routes/webhooks.py`  
**Requirements:** 1.1, 1.5

## Features

### 1. Message Deduplication

**Purpose:** Prevent processing the same message multiple times due to webhook retries or network issues.

**Implementation:**
- In-memory cache of processed message IDs
- 5-minute TTL (Time To Live)
- Automatic cleanup of expired entries

**Configuration:**
```python
# Message deduplication cache (5 minutes TTL)
_processed_messages: Dict[str, datetime] = {}
_DEDUP_TTL_SECONDS = 300
```

**How it works:**
1. When a message arrives, check if message ID exists in cache
2. If found and not expired (< 5 minutes old), skip processing
3. If not found or expired, process message and add to cache
4. Periodically clean up expired entries

**Benefits:**
- Prevents duplicate responses to users
- Avoids wasted LLM API calls
- Reduces database write load
- Improves cost efficiency

### 2. Message Batching

**Purpose:** Batch multiple rapid messages from the same user into a single processing cycle.

**Implementation:**
- 7-second delay before processing
- Combines multiple messages into one context
- Per-conversation processing locks
- Automatic message aggregation

**Configuration:**
```python
# Message batching (7 seconds delay)
@dataclass
class PendingMessage:
    content: str
    timestamp: int
    sender: Dict[str, Any]

_pending_messages: Dict[str, List[PendingMessage]] = {}
_processing_locks: Dict[str, asyncio.Lock] = {}
MESSAGE_PROCESSING_DELAY_SECONDS = 7
```

**How it works:**
1. When a message arrives, add to pending queue for conversation
2. Start 7-second timer
3. If more messages arrive within 7 seconds, add to same queue
4. After 7 seconds, process all messages together
5. Combine messages into single context for agent

**Benefits:**
- Better context understanding (user sends info in multiple messages)
- Reduces number of LLM calls
- Improves response quality
- Lowers operational costs

## Data Structures

### PendingMessage

```python
@dataclass
class PendingMessage:
    content: str          # Message text
    timestamp: int        # Unix timestamp
    sender: Dict[str, Any]  # Sender metadata
```

### Global State

```python
# Deduplication cache: message_id -> timestamp
_processed_messages: Dict[str, datetime] = {}

# Batching queue: conversation_id -> [messages]
_pending_messages: Dict[str, List[PendingMessage]] = {}

# Processing locks: conversation_id -> Lock
_processing_locks: Dict[str, asyncio.Lock] = {}
```

## Configuration

### Deduplication TTL

**Default:** 300 seconds (5 minutes)

**Rationale:**
- Chatwoot webhook retries typically happen within 1-2 minutes
- 5 minutes provides safety margin
- Balances memory usage vs. duplicate prevention

**To modify:**
```python
_DEDUP_TTL_SECONDS = 300  # Change to desired seconds
```

### Batching Delay

**Default:** 7 seconds

**Rationale:**
- Users typically send multiple messages within 5-10 seconds
- 7 seconds captures most multi-message inputs
- Not too long to feel unresponsive
- Balances batching efficiency vs. response time

**To modify:**
```python
MESSAGE_PROCESSING_DELAY_SECONDS = 7  # Change to desired seconds
```

## Usage Examples

### Example 1: Duplicate Message Prevention

**Scenario:** Chatwoot sends same message twice due to retry

```
Message 1: ID=12345, content="Olá", timestamp=10:00:00
Message 2: ID=12345, content="Olá", timestamp=10:00:02 (retry)
```

**Behavior:**
1. Message 1 arrives → Process normally
2. Add ID=12345 to cache with timestamp
3. Message 2 arrives → Check cache
4. ID=12345 found, age=2s (< 5min) → Skip processing
5. Return 200 OK without processing

**Result:** User receives only one response

### Example 2: Message Batching

**Scenario:** User sends multiple messages rapidly

```
10:00:00 - "Olá"
10:00:03 - "Gostaria de agendar"
10:00:05 - "Depilação a laser"
```

**Behavior:**
1. Message 1 arrives → Add to pending queue, start 7s timer
2. Message 2 arrives (3s later) → Add to same queue
3. Message 3 arrives (5s later) → Add to same queue
4. Timer expires at 10:00:07
5. Process all 3 messages together as context
6. Agent sees: "Olá\nGostaria de agendar\nDepilação a laser"

**Result:** Agent has full context, provides better response

### Example 3: Mixed Scenario

**Scenario:** Batching + deduplication

```
10:00:00 - Message A (ID=100)
10:00:02 - Message A (ID=100, duplicate)
10:00:04 - Message B (ID=101)
```

**Behavior:**
1. Message A arrives → Add to pending queue
2. Duplicate A arrives → Check cache, skip
3. Message B arrives → Add to pending queue
4. Timer expires → Process A + B together

**Result:** Efficient processing with no duplicates

## Memory Management

### Deduplication Cache Cleanup

**Strategy:** Lazy cleanup on access

```python
def _cleanup_expired_messages():
    """Remove messages older than TTL."""
    now = datetime.utcnow()
    expired = [
        msg_id for msg_id, ts in _processed_messages.items()
        if (now - ts).total_seconds() > _DEDUP_TTL_SECONDS
    ]
    for msg_id in expired:
        del _processed_messages[msg_id]
```

**Trigger:** Called before checking/adding messages

**Memory impact:**
- ~100 bytes per message ID
- Max ~1000 messages in 5 minutes (typical)
- Total: ~100KB memory usage

### Batching Queue Cleanup

**Strategy:** Clear after processing

```python
async def _process_batched_messages(conversation_id: str):
    """Process and clear batched messages."""
    messages = _pending_messages.pop(conversation_id, [])
    # Process messages...
    # Queue automatically cleared
```

**Memory impact:**
- ~500 bytes per pending message
- Max ~10 conversations with pending messages
- Total: ~5KB memory usage

## Performance Considerations

### Deduplication

**Lookup time:** O(1) - Dictionary lookup  
**Memory:** O(n) - Linear with message count  
**Cleanup:** O(n) - Linear scan of cache

**Optimization:**
- Use message ID as key (fast lookup)
- Lazy cleanup (no background threads)
- TTL prevents unbounded growth

### Batching

**Queue time:** O(1) - Append to list  
**Processing:** O(n) - Linear with batch size  
**Lock contention:** Minimal (per-conversation locks)

**Optimization:**
- Per-conversation queues (no global lock)
- Async processing (non-blocking)
- Automatic cleanup after processing

## Monitoring

### Metrics to Track

1. **Deduplication Rate**
   - Formula: (duplicates_skipped / total_messages) × 100
   - Target: < 5% (indicates healthy webhook delivery)
   - Alert: > 20% (indicates webhook retry issues)

2. **Batch Size Distribution**
   - Track: Average messages per batch
   - Target: 1.5-2.0 (indicates effective batching)
   - Alert: > 5 (indicates user confusion or issues)

3. **Processing Delay**
   - Track: Time from first message to processing
   - Target: ~7 seconds (configured delay)
   - Alert: > 15 seconds (indicates processing backlog)

### Logging

**Deduplication events:**
```python
logger.debug(
    "duplicate_message_skipped",
    message_id=message_id,
    conversation_id=conversation_id,
    age_seconds=age
)
```

**Batching events:**
```python
logger.info(
    "messages_batched",
    conversation_id=conversation_id,
    batch_size=len(messages),
    delay_seconds=delay
)
```

## Testing

### Unit Tests

```python
def test_deduplication():
    """Test duplicate message prevention."""
    # Process message once
    result1 = process_message(msg_id="123", content="Hello")
    assert result1.processed == True
    
    # Try to process again
    result2 = process_message(msg_id="123", content="Hello")
    assert result2.processed == False
    assert result2.reason == "duplicate"

def test_batching():
    """Test message batching."""
    # Send 3 messages rapidly
    add_message(conv_id="1", content="A")
    add_message(conv_id="1", content="B")
    add_message(conv_id="1", content="C")
    
    # Wait for batch processing
    await asyncio.sleep(8)
    
    # Verify batched
    assert get_batch_size(conv_id="1") == 3
```

### Integration Tests

```python
async def test_webhook_deduplication():
    """Test webhook with duplicate messages."""
    payload = create_webhook_payload(msg_id="123")
    
    # Send twice
    response1 = await client.post("/webhook/chatwoot", json=payload)
    response2 = await client.post("/webhook/chatwoot", json=payload)
    
    # Both return 200
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # But only one processed
    assert get_processing_count() == 1
```

## Troubleshooting

### Issue: Messages Not Being Batched

**Symptoms:**
- Each message processed individually
- High LLM API call count
- Increased costs

**Possible causes:**
1. Delay too short for user typing speed
2. Messages from different conversations
3. Processing locks not working

**Solutions:**
1. Increase `MESSAGE_PROCESSING_DELAY_SECONDS`
2. Verify conversation ID extraction
3. Check lock implementation

### Issue: Legitimate Messages Being Skipped

**Symptoms:**
- User reports messages not answered
- Logs show "duplicate_message_skipped"
- Message IDs are different

**Possible causes:**
1. TTL too long
2. Message ID collision
3. Cache not being cleaned

**Solutions:**
1. Reduce `_DEDUP_TTL_SECONDS`
2. Verify message ID uniqueness
3. Implement active cache cleanup

### Issue: High Memory Usage

**Symptoms:**
- Memory usage growing over time
- Cache size increasing
- OOM errors

**Possible causes:**
1. Cache not being cleaned
2. TTL too long
3. High message volume

**Solutions:**
1. Implement periodic cleanup
2. Reduce TTL
3. Add cache size limits

## Future Enhancements

### 1. Redis-Based Deduplication

**Benefits:**
- Persistent across restarts
- Shared across multiple instances
- Automatic TTL expiration

**Implementation:**
```python
async def is_duplicate(message_id: str) -> bool:
    key = f"dedup:{message_id}"
    exists = await redis_client.exists(key)
    if not exists:
        await redis_client.setex(key, _DEDUP_TTL_SECONDS, "1")
    return exists
```

### 2. Adaptive Batching Delay

**Benefits:**
- Faster response for single messages
- Better batching for rapid messages
- Improved user experience

**Implementation:**
```python
def calculate_delay(conversation_id: str) -> int:
    """Calculate delay based on message history."""
    history = get_message_history(conversation_id)
    avg_interval = calculate_avg_interval(history)
    
    if avg_interval < 3:
        return 10  # User types fast, wait longer
    else:
        return 5   # User types slow, respond faster
```

### 3. Batch Size Limits

**Benefits:**
- Prevent context overflow
- Control LLM costs
- Better error handling

**Implementation:**
```python
MAX_BATCH_SIZE = 5

async def add_to_batch(conversation_id: str, message: str):
    if len(_pending_messages[conversation_id]) >= MAX_BATCH_SIZE:
        # Process immediately
        await process_batch(conversation_id)
    
    _pending_messages[conversation_id].append(message)
```

## Best Practices

1. **Monitor deduplication rate** - High rate indicates webhook issues
2. **Track batch sizes** - Understand user behavior patterns
3. **Log all skipped messages** - For debugging and auditing
4. **Test with production-like load** - Verify performance at scale
5. **Document configuration changes** - Track delay/TTL adjustments
6. **Set up alerts** - For abnormal deduplication or batching patterns

## Conclusion

Message deduplication and batching are critical features for:
- **Reliability:** Prevent duplicate processing
- **Efficiency:** Reduce API calls and costs
- **Quality:** Better context understanding
- **Performance:** Optimize resource usage

The current implementation provides a solid foundation with room for future enhancements based on production usage patterns.
