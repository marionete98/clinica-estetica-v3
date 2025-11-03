"""
Test script for FAQ Redis cache integration.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.faq import create_faq_agent
from config.settings import settings
from config.redis_client import redis_client


async def test_faq_redis_cache():
    """Test FAQ agent with Redis cache."""
    
    print("=" * 60)
    print("FAQ Redis Cache Integration Test")
    print("=" * 60)
    
    # 1. Check Redis connection
    print("\n1. Testing Redis connection...")
    if redis_client.health_check():
        print("   ✅ Redis connection healthy")
    else:
        print("   ❌ Redis connection failed")
        return
    
    # 2. Create FAQ agent with cache enabled
    print("\n2. Creating FAQ agent with Redis cache...")
    llm_config = settings.get_llm_config()
    faq_agent = create_faq_agent(
        llm_config,
        enable_cache=True,
        cache_ttl_seconds=300,  # 5 minutes for testing
        cache_max_size=50
    )
    print("   ✅ FAQ agent created")
    
    # 3. Test cache miss (first query)
    print("\n3. Testing cache MISS (first query)...")
    question1 = "Quanto custa depilação a laser?"
    result1 = await faq_agent.answer_question(question1)
    print(f"   Question: {question1}")
    print(f"   Cached: {result1.get('cached', False)}")
    print(f"   Confidence: {result1.get('confidence')}")
    print(f"   Answer preview: {result1.get('answer', '')[:100]}...")
    
    # 4. Test cache hit (same query)
    print("\n4. Testing cache HIT (same query)...")
    result2 = await faq_agent.answer_question(question1)
    print(f"   Question: {question1}")
    print(f"   Cached: {result2.get('cached', False)}")
    if result2.get('cached'):
        print("   ✅ Cache hit successful")
    else:
        print("   ⚠️  Expected cache hit but got miss")
    
    # 5. Test cache stats
    print("\n5. Checking cache statistics...")
    stats = faq_agent.get_cache_stats()
    if stats:
        print(f"   Current size: {stats.get('current_size', 0)}")
        print(f"   Max size: {stats.get('max_size', 0)}")
        print(f"   Hits: {stats.get('hits', 0)}")
        print(f"   Misses: {stats.get('misses', 0)}")
        print(f"   Hit rate: {stats.get('hit_rate', 0):.1%}")
        print(f"   TTL: {stats.get('ttl_seconds', 0)}s")
    else:
        print("   ⚠️  Cache stats not available")
    
    # 6. Test different question (cache miss)
    print("\n6. Testing different question (cache miss)...")
    question2 = "Qual o horário de funcionamento?"
    result3 = await faq_agent.answer_question(question2)
    print(f"   Question: {question2}")
    print(f"   Cached: {result3.get('cached', False)}")
    print(f"   Confidence: {result3.get('confidence')}")
    
    # 7. Test cache normalization (similar question)
    print("\n7. Testing cache normalization...")
    question3 = "QUANTO CUSTA DEPILAÇÃO A LASER?"  # Same question, different case
    result4 = await faq_agent.answer_question(question3)
    print(f"   Question: {question3}")
    print(f"   Cached: {result4.get('cached', False)}")
    if result4.get('cached'):
        print("   ✅ Cache normalization working")
    else:
        print("   ⚠️  Cache normalization may need adjustment")
    
    # 8. Final cache stats
    print("\n8. Final cache statistics...")
    final_stats = faq_agent.get_cache_stats()
    if final_stats:
        print(f"   Current size: {final_stats.get('current_size', 0)}")
        print(f"   Hits: {final_stats.get('hits', 0)}")
        print(f"   Misses: {final_stats.get('misses', 0)}")
        print(f"   Hit rate: {final_stats.get('hit_rate', 0):.1%}")
    
    # 9. Test cache clear
    print("\n9. Testing cache clear...")
    faq_agent.clear_cache()
    cleared_stats = faq_agent.get_cache_stats()
    print(f"   Current size after clear: {cleared_stats.get('current_size', 0)}")
    print(f"   Hits after clear: {cleared_stats.get('hits', 0)}")
    print(f"   Misses after clear: {cleared_stats.get('misses', 0)}")
    
    # 10. Cleanup
    print("\n10. Cleaning up...")
    await faq_agent.cleanup()
    print("   ✅ Cleanup complete")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_faq_redis_cache())
