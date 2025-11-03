#!/usr/bin/env python3
"""
Script to inspect Redis configuration and data structure.
Shows how the knowledge base cache is organized internally.
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from config.redis_client import redis_client


def inspect_redis_info():
    """Inspect Redis server information and configuration."""
    print("🔍 REDIS SERVER INFORMATION")
    print("=" * 60)
    
    try:
        # Get Redis info
        info = redis_client.client.info()
        
        print(f"📊 Redis Version: {info.get('redis_version', 'Unknown')}")
        print(f"🏠 Redis Mode: {info.get('redis_mode', 'Unknown')}")
        print(f"💾 Used Memory: {info.get('used_memory_human', 'Unknown')}")
        print(f"🔗 Connected Clients: {info.get('connected_clients', 'Unknown')}")
        print(f"⏱️  Uptime: {info.get('uptime_in_seconds', 0)} seconds")
        
        # Memory usage
        if 'used_memory' in info and 'maxmemory' in info:
            used_mb = info['used_memory'] / (1024 * 1024)
            max_mb = info['maxmemory'] / (1024 * 1024) if info['maxmemory'] > 0 else 0
            print(f"💾 Memory Usage: {used_mb:.2f} MB" + (f" / {max_mb:.2f} MB" if max_mb > 0 else " (no limit)"))
        
        # Database info
        db_info = {}
        for key, value in info.items():
            if key.startswith('db'):
                db_info[key] = value
        
        if db_info:
            print(f"\n📚 Databases:")
            for db, stats in db_info.items():
                print(f"   {db}: {stats}")
        
        # Check for Redis modules
        modules = redis_client.client.execute_command('MODULE', 'LIST')
        if modules:
            print(f"\n🧩 Redis Modules:")
            for module in modules:
                print(f"   - {module}")
        else:
            print(f"\n🧩 Redis Modules: None (standard Redis)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting Redis info: {e}")
        return False


def inspect_kb_cache_structure():
    """Inspect knowledge base cache structure."""
    print("\n🗂️  KNOWLEDGE BASE CACHE STRUCTURE")
    print("=" * 60)
    
    try:
        # Get all KB-related keys
        kb_keys = redis_client.client.keys("kb:*")
        template_keys = redis_client.client.keys("template:*")
        conv_keys = redis_client.client.keys("conv:*")
        
        print(f"📚 Knowledge Base Keys: {len(kb_keys)}")
        print(f"📄 Template Keys: {len(template_keys)}")
        print(f"💬 Conversation Keys: {len(conv_keys)}")
        
        # Analyze KB keys by type
        kb_entries = [k for k in kb_keys if k.startswith("kb:") and not k.startswith("kb:index:") and k != "kb:metadata"]
        kb_indexes = [k for k in kb_keys if k.startswith("kb:index:")]
        kb_metadata = [k for k in kb_keys if k == "kb:metadata"]
        
        print(f"\n📊 KB Key Breakdown:")
        print(f"   📖 Entries: {len(kb_entries)}")
        print(f"   🔍 Indexes: {len(kb_indexes)}")
        print(f"   ⚙️  Metadata: {len(kb_metadata)}")
        
        # Show sample keys
        if kb_entries:
            print(f"\n📖 Sample KB Entry Keys:")
            for key in kb_entries[:5]:
                ttl = redis_client.client.ttl(key)
                print(f"   {key} (TTL: {ttl}s)")
        
        if kb_indexes:
            print(f"\n🔍 Sample Index Keys:")
            for key in kb_indexes[:10]:
                members_count = redis_client.client.scard(key)
                ttl = redis_client.client.ttl(key)
                print(f"   {key} ({members_count} entries, TTL: {ttl}s)")
        
        if template_keys:
            print(f"\n📄 Template Keys:")
            for key in template_keys[:5]:
                ttl = redis_client.client.ttl(key)
                print(f"   {key} (TTL: {ttl}s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error inspecting cache structure: {e}")
        return False


def inspect_sample_data():
    """Inspect sample data from cache."""
    print("\n📋 SAMPLE CACHE DATA")
    print("=" * 60)
    
    try:
        # Get metadata
        metadata = redis_client.get_value("kb:metadata")
        if metadata:
            print("⚙️  Cache Metadata:")
            print(f"   Last Sync: {metadata.get('last_sync', 'Unknown')}")
            print(f"   Sync Interval: {metadata.get('sync_interval', 'Unknown')}s")
            print(f"   Cache TTL: {metadata.get('cache_ttl', 'Unknown')}s")
            print(f"   Version: {metadata.get('version', 'Unknown')}")
        
        # Get sample KB entry
        kb_keys = redis_client.client.keys("kb:*")
        kb_entries = [k for k in kb_keys if k.startswith("kb:") and not k.startswith("kb:index:") and k != "kb:metadata"]
        
        if kb_entries:
            sample_key = kb_entries[0]
            sample_data = redis_client.get_value(sample_key)
            
            print(f"\n📖 Sample KB Entry ({sample_key}):")
            if sample_data:
                print(f"   ID: {sample_data.get('id', 'Unknown')}")
                print(f"   Title: {sample_data.get('title', 'Unknown')}")
                print(f"   Category: {sample_data.get('category', 'Unknown')}")
                print(f"   Keywords: {sample_data.get('keywords', [])}")
                print(f"   Content Length: {len(sample_data.get('content', ''))} chars")
                print(f"   Cached At: {sample_data.get('cached_at', 'Unknown')}")
        
        # Get sample template
        template_keys = redis_client.client.keys("template:*")
        if template_keys:
            sample_template_key = template_keys[0]
            sample_template = redis_client.get_value(sample_template_key)
            
            print(f"\n📄 Sample Template ({sample_template_key}):")
            if sample_template:
                print(f"   Name: {sample_template.get('name', 'Unknown')}")
                print(f"   Variables: {sample_template.get('variables', [])}")
                print(f"   Category: {sample_template.get('category', 'Unknown')}")
                print(f"   Content Length: {len(sample_template.get('content', ''))} chars")
        
        # Get sample index
        index_keys = redis_client.client.keys("kb:index:*")
        if index_keys:
            sample_index_key = index_keys[0]
            index_members = redis_client.client.smembers(sample_index_key)
            
            print(f"\n🔍 Sample Index ({sample_index_key}):")
            print(f"   Entry IDs: {list(index_members)[:5]}{'...' if len(index_members) > 5 else ''}")
            print(f"   Total Entries: {len(index_members)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error inspecting sample data: {e}")
        return False


def inspect_memory_usage():
    """Inspect memory usage by key patterns."""
    print("\n💾 MEMORY USAGE ANALYSIS")
    print("=" * 60)
    
    try:
        # Get memory usage by key pattern
        patterns = [
            ("kb:*", "Knowledge Base"),
            ("template:*", "Templates"),
            ("conv:*", "Conversations"),
            ("kb:index:*", "KB Indexes"),
            ("kb:metadata", "KB Metadata")
        ]
        
        total_memory = 0
        
        for pattern, description in patterns:
            keys = redis_client.client.keys(pattern)
            pattern_memory = 0
            
            for key in keys:
                try:
                    # Get memory usage for each key
                    memory = redis_client.client.memory_usage(key)
                    if memory:
                        pattern_memory += memory
                except:
                    # Fallback: estimate based on serialized size
                    try:
                        value = redis_client.client.get(key)
                        if value:
                            pattern_memory += len(value.encode('utf-8'))
                    except:
                        pass
            
            total_memory += pattern_memory
            
            print(f"📊 {description}:")
            print(f"   Keys: {len(keys)}")
            print(f"   Memory: {pattern_memory / 1024:.2f} KB")
        
        print(f"\n💾 Total Cache Memory: {total_memory / 1024:.2f} KB ({total_memory / (1024*1024):.2f} MB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing memory usage: {e}")
        return False


def inspect_key_expiration():
    """Inspect key expiration and TTL settings."""
    print("\n⏰ KEY EXPIRATION ANALYSIS")
    print("=" * 60)
    
    try:
        # Check TTL for different key types
        key_types = [
            ("kb:", "KB Entries"),
            ("template:", "Templates"),
            ("kb:index:", "KB Indexes"),
            ("conv:", "Conversations")
        ]
        
        for prefix, description in key_types:
            keys = redis_client.client.keys(f"{prefix}*")
            
            if not keys:
                continue
            
            ttls = []
            for key in keys[:10]:  # Sample first 10 keys
                ttl = redis_client.client.ttl(key)
                if ttl >= 0:
                    ttls.append(ttl)
            
            if ttls:
                avg_ttl = sum(ttls) / len(ttls)
                min_ttl = min(ttls)
                max_ttl = max(ttls)
                
                print(f"⏱️  {description}:")
                print(f"   Sample Size: {len(ttls)} keys")
                print(f"   Average TTL: {avg_ttl:.0f}s ({avg_ttl/3600:.1f}h)")
                print(f"   Min TTL: {min_ttl}s")
                print(f"   Max TTL: {max_ttl}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing key expiration: {e}")
        return False


def test_redis_operations():
    """Test basic Redis operations."""
    print("\n🧪 REDIS OPERATIONS TEST")
    print("=" * 60)
    
    try:
        test_key = "redis_inspect_test"
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "test": "data",
            "number": 42
        }
        
        # Test SET
        print("🔧 Testing SET operation...")
        success = redis_client.set_value(test_key, test_data, ttl=60)
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        
        # Test GET
        print("🔧 Testing GET operation...")
        retrieved = redis_client.get_value(test_key)
        if retrieved and retrieved.get("test") == "data":
            print("   Result: ✅ Success")
        else:
            print("   Result: ❌ Failed")
        
        # Test TTL
        print("🔧 Testing TTL...")
        ttl = redis_client.client.ttl(test_key)
        print(f"   TTL: {ttl}s ({'✅ Valid' if 0 < ttl <= 60 else '❌ Invalid'})")
        
        # Test DELETE
        print("🔧 Testing DELETE operation...")
        deleted = redis_client.delete_key(test_key)
        print(f"   Result: {'✅ Success' if deleted else '❌ Failed'}")
        
        # Test SET operations (for indexes)
        print("🔧 Testing SET operations (for indexes)...")
        test_set_key = "test_set"
        redis_client.client.sadd(test_set_key, "item1", "item2", "item3")
        members = redis_client.client.smembers(test_set_key)
        redis_client.client.delete(test_set_key)
        
        if len(members) == 3:
            print("   Result: ✅ Success")
        else:
            print("   Result: ❌ Failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Redis operations: {e}")
        return False


def main():
    """Main inspection function."""
    print("🔍 REDIS CONFIGURATION AND DATA INSPECTION")
    print("=" * 80)
    print(f"🕐 Inspection Time: {datetime.now().isoformat()}")
    
    tests = [
        ("Redis Server Info", inspect_redis_info),
        ("KB Cache Structure", inspect_kb_cache_structure),
        ("Sample Data", inspect_sample_data),
        ("Memory Usage", inspect_memory_usage),
        ("Key Expiration", inspect_key_expiration),
        ("Redis Operations", test_redis_operations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"💥 {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 INSPECTION SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\n🏁 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Redis is configured and working perfectly!")
    elif passed >= total * 0.8:
        print("👍 Redis is mostly working well.")
    else:
        print("⚠️  Redis has some issues that need attention.")


if __name__ == "__main__":
    main()