#!/usr/bin/env python3
"""Test cached KB tools."""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from tools.kb_tools_cached import search_knowledge_base


async def main():
    print("Testing Cached KB Tools...")
    
    results = await search_knowledge_base("depilação laser", top_k=2)
    
    if results:
        print(f"✅ Found {len(results)} results:")
        for result in results:
            print(f"  - {result.get('title', 'No title')}")
    else:
        print("❌ No results found")


if __name__ == "__main__":
    asyncio.run(main())