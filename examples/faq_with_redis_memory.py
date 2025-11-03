"""
Example: FAQ Agent with AutoGen RedisMemory for conversation history.

This example demonstrates how to use both:
1. RedisFAQCache - for response caching (custom)
2. RedisMemory - for conversation history (AutoGen native)

Requirements:
- pip install autogen-ext[redis]
"""

import asyncio
from autogen_ext.memory import RedisMemory
from agents.faq import create_faq_agent
from config.settings import settings


async def main():
    """
    Example of FAQ agent with both response cache and conversation memory.
    """
    
    print("=" * 60)
    print("FAQ Agent with Redis Memory Example")
    print("=" * 60)
    
    # 1. Create Redis memory for conversation history
    print("\n1. Creating Redis memory for conversation history...")
    conversation_memory = RedisMemory(
        redis_url=settings.redis_url,
        namespace="faq_conversations",
        ttl=86400  # 24 hours
    )
    print("   ✅ Redis memory created")
    
    # 2. Create FAQ agent with response cache
    print("\n2. Creating FAQ agent with response cache...")
    llm_config = settings.get_llm_config()
    faq_agent = create_faq_agent(
        llm_config,
        enable_cache=True,
        cache_ttl_seconds=3600  # 1 hour
    )
    print("   ✅ FAQ agent created with cache")
    
    # 3. Attach memory to agent (optional)
    print("\n3. Attaching conversation memory to agent...")
    faq_agent.agent.memory = conversation_memory
    print("   ✅ Memory attached")
    
    # 4. Test conversation with memory
    print("\n4. Testing conversation with memory...")
    
    conversation_id = "test_conversation_123"
    
    # First question
    print("\n   Question 1: Quanto custa depilação a laser?")
    result1 = await faq_agent.answer_question(
        question="Quanto custa depilação a laser?",
        contact_name="João"
    )
    print(f"   Cached: {result1.get('cached', False)}")
    print(f"   Answer: {result1.get('answer', '')[:100]}...")
    
    # Second question (same - should be cached)
    print("\n   Question 2: Quanto custa depilação a laser? (same)")
    result2 = await faq_agent.answer_question(
        question="Quanto custa depilação a laser?",
        contact_name="João"
    )
    print(f"   Cached: {result2.get('cached', False)}")
    if result2.get('cached'):
        print("   ✅ Response served from cache!")
    
    # Third question (different)
    print("\n   Question 3: Qual o horário de funcionamento?")
    result3 = await faq_agent.answer_question(
        question="Qual o horário de funcionamento?",
        contact_name="João"
    )
    print(f"   Cached: {result3.get('cached', False)}")
    print(f"   Answer: {result3.get('answer', '')[:100]}...")
    
    # 5. Check cache statistics
    print("\n5. Cache statistics:")
    stats = faq_agent.get_cache_stats()
    if stats:
        print(f"   Current size: {stats.get('current_size', 0)}")
        print(f"   Hits: {stats.get('hits', 0)}")
        print(f"   Misses: {stats.get('misses', 0)}")
        print(f"   Hit rate: {stats.get('hit_rate', 0):.1%}")
    
    # 6. Cleanup
    print("\n6. Cleaning up...")
    await faq_agent.cleanup()
    print("   ✅ Cleanup complete")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
    
    print("\n📝 Summary:")
    print("   - RedisFAQCache: Caches FAQ responses (custom)")
    print("   - RedisMemory: Stores conversation history (AutoGen)")
    print("   - Both work together for optimal performance")


if __name__ == "__main__":
    asyncio.run(main())
