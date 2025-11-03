#!/usr/bin/env python3
"""
Script to test Redis Knowledge Base Cache functionality.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from services.container import get_kb_cache_service, get_redis_client
from tools.kb_tools_cached import search_knowledge_base, get_message_template


async def test_cache_initialization():
    """Test cache initialization."""
    print("🔄 Testing cache initialization...")
    cache_service = get_kb_cache_service()
    try:
        success = await cache_service.initialize_cache()
        
        if success:
            stats = await cache_service.get_cache_stats()
            print(f"✅ Cache initialized successfully!")
            print(f"   📊 Entries: {stats.total_entries}")
            print(f"   📄 Templates: {stats.total_templates}")
            return True
        else:
            print("❌ Cache initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Cache initialization error: {e}")
        return False


async def test_search_performance():
    """Test search performance."""
    print("\n🚀 Testing search performance...")
    
    test_queries = [
        "depilação laser preço",
        "harmonização facial botox",
        "política cancelamento"
    ]
    
    total_time = 0
    successful_searches = 0
    
    for query in test_queries:
        try:
            start_time = time.time()
            results = await search_knowledge_base(query, top_k=3)
            end_time = time.time()
            
            search_time = (end_time - start_time) * 1000  # Convert to ms
            total_time += search_time
            
            if results:
                successful_searches += 1
                print(f"   ✅ '{query}': {len(results)} results in {search_time:.1f}ms")
            else:
                print(f"   ⚠️  '{query}': No results found")
                
        except Exception as e:
            print(f"   ❌ '{query}': Error - {e}")
    
    if successful_searches > 0:
        avg_time = total_time / successful_searches
        print(f"\n📈 Average response time: {avg_time:.1f}ms")
        
        if avg_time < 100:
            print("   🎉 Excellent performance! (< 100ms)")
        elif avg_time < 200:
            print("   👍 Good performance (< 200ms)")
        else:
            print("   ⚠️  Performance could be improved (> 200ms)")
    
    return successful_searches > 0


async def test_redis_connectivity():
    """Test Redis connectivity."""
    print("\n🔗 Testing Redis connectivity...")
    redis_client = get_redis_client()
    try:
        test_key = "kb_cache_test"
        test_value = {"test": "data", "timestamp": time.time()}
        
        # Set value
        success = await redis_client.set_value(test_key, test_value, ttl=60)
        
        if success:
            print("✅ Redis write operation successful")
            
            # Get value
            retrieved = await redis_client.get_value(test_key)
            
            if retrieved and retrieved.get("test") == "data":
                print("✅ Redis read operation successful")
                await redis_client.delete_key(test_key)
                return True
            else:
                print("❌ Redis read operation failed")
                return False
        else:
            print("❌ Redis write operation failed")
            return False
            
    except Exception as e:
        print(f"❌ Redis connectivity error: {e}")
        return False


async def run_tests():
    """Run cache test suite."""
    print("🧪 REDIS KNOWLEDGE BASE CACHE TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Redis Connectivity", test_redis_connectivity),
        ("Cache Initialization", test_cache_initialization),
        ("Search Performance", test_search_performance)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            success = await test_func()
            if success:
                passed_tests += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {e}")
    
    # Final summary
    print(f"\n{'='*50}")
    print(f"🏁 TEST RESULTS: {passed_tests}/{total_tests} PASSED")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Cache is working perfectly.")
    else:
        print("⚠️  Some tests failed. Cache needs attention.")


if __name__ == "__main__":
    asyncio.run(run_tests())
