#!/usr/bin/env python3
"""
Validation script for Chatwoot improvements.
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def check_database_migration():
    """Check if database migration was applied."""
    try:
        from config.supabase_client import supabase_client
        result = supabase_client.client.table("sessions").select("automation_paused").limit(1).execute()
        return True, "Column 'automation_paused' exists"
    except Exception as e:
        return False, f"Migration not applied: {str(e)[:100]}"


def check_environment_variables():
    """Check if new environment variables are configured."""
    try:
        from config.settings import settings
        
        if not hasattr(settings, 'message_dedup_ttl_seconds'):
            return False, "MESSAGE_DEDUP_TTL_SECONDS not configured"
        
        if not hasattr(settings, 'message_processing_delay_seconds'):
            return False, "MESSAGE_PROCESSING_DELAY_SECONDS not configured"
        
        return True, f"Dedup TTL: {settings.message_dedup_ttl_seconds}s, Delay: {settings.message_processing_delay_seconds}s"
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"


def check_code_changes():
    """Check if code changes are present."""
    try:
        from routes.webhooks import is_duplicate_message, collect_and_process_messages
        from routes.api import return_conversation_to_ai
        return True, "All functions present"
    except ImportError as e:
        return False, f"Missing: {str(e)}"


async def check_redis():
    """Check Redis connectivity."""
    try:
        from config.redis_client import get_redis_client
        redis = get_redis_client()
        await redis.set("test", "ok", ex=10)
        result = await redis.get("test")
        await redis.delete("test")
        return result == "ok", "Redis operational" if result == "ok" else "Redis test failed"
    except Exception as e:
        return False, f"Redis error: {str(e)[:100]}"


async def main():
    """Run all checks."""
    print("🔍 Validating Chatwoot Improvements...\n")
    
    checks = [
        ("Database Migration", await check_database_migration()),
        ("Environment Variables", check_environment_variables()),
        ("Code Changes", check_code_changes()),
        ("Redis Connectivity", await check_redis()),
    ]
    
    print("="*70)
    all_passed = True
    
    for name, (passed, message) in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {message}")
        if not passed:
            all_passed = False
    
    print("="*70)
    print("\n✅ ALL CHECKS PASSED" if all_passed else "\n❌ SOME CHECKS FAILED")
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
