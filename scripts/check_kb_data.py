#!/usr/bin/env python3
"""Check KB data."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config.supabase_client import supabase_client

def main():
    print("Checking KB data...")
    
    try:
        supabase = supabase_client.client
        response = supabase.table('knowledge_base').select('id, title').execute()
        
        print(f"📚 KB entries found: {len(response.data)}")
        
        if response.data:
            print("Sample entries:")
            for item in response.data[:5]:
                print(f"  - {item['title']}")
        else:
            print("⚠️  No KB entries found. Need to populate KB first.")
            print("Run: py scripts/populate_knowledge_base.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()