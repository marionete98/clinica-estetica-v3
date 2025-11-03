#!/usr/bin/env python3
"""Test simple KB cache."""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from services.container import get_kb_cache_service


async def main():
    print("Testing Simple KB Cache...")
    
    cache_service = get_kb_cache_service()
    success = await cache_service.initialize_cache()
    
    if success:
        print("✅ Cache initialized!")
        stats = await cache_service.get_cache_stats()
        print(f"📊 Entries: {stats.total_entries}")
    else:
        print("❌ Cache failed")


if __name__ == "__main__":
    asyncio.run(main())
