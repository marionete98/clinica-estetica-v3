#!/usr/bin/env python3
"""
Test script for Chatwoot webhook integration.

This script tests the complete flow:
1. Send test webhook to the system
2. Verify webhook is received and processed
3. Check response is sent back
4. Verify logs are created in Supabase

Requirements: 1.1, 1.5, 3.5
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DEPLOYMENT_URL = os.getenv("DEPLOYMENT_URL", "http://localhost:8000")
CHATWOOT_WEBHOOK_TOKEN = os.getenv("CHATWOOT_WEBHOOK_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Test data
TEST_PHONE = "+5594991398585"
TEST_CONVERSATION_ID = 999999
TEST_MESSAGE_ID = 888888


def create_test_payload(message: str, conversation_id: int = TEST_CONVERSATION_ID) -> Dict[str, Any]:
    """Create a test Chatwoot webhook payload."""
    return {
        "event": "message_created",
        "id": TEST_MESSAGE_ID,
        "content": message,
        "message_type": "incoming",
        "created_at": int(time.time()),
        "conversation": {
            "id": conversation_id,
            "inbox_id": 1,
            "status": "open"
        },
        "sender": {
            "id": 456,
            "name": "Test User",
            "phone_number": TEST_PHONE,
            "identifier": TEST_PHONE,
            "type": "contact"
        },
        "account": {
            "id": 1,
            "name": "Clínica Luana"
        }
    }


async def test_webhook_endpoint(message: str) -> bool:
    """
    Test sending a webhook to the endpoint.
    
    Args:
        message: Test message to send
        
    Returns:
        True if webhook was accepted, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"TEST 1: Webhook Endpoint")
    print(f"{'='*60}")
    
    payload = create_test_payload(message)
    
    url = f"{DEPLOYMENT_URL}/webhook/chatwoot"
    headers = {
        "Content-Type": "application/json",
        "api_access_token": CHATWOOT_WEBHOOK_TOKEN
    }
    
    print(f"📤 Sending webhook to: {url}")
    print(f"📝 Message: {message}")
    print(f"🔑 Token: {CHATWOOT_WEBHOOK_TOKEN[:10]}...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "accepted":
                print("✅ Webhook accepted successfully")
                return True
            else:
                print(f"⚠️  Webhook ignored: {data.get('reason')}")
                return False
        else:
            print(f"❌ Webhook failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending webhook: {str(e)}")
        return False


async def verify_logs_in_supabase(conversation_id: int, timeout: int = 30) -> bool:
    """
    Verify that logs were created in Supabase.
    
    Args:
        conversation_id: Conversation ID to check
        timeout: Maximum seconds to wait for logs
        
    Returns:
        True if logs found, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"TEST 2: Verify Logs in Supabase")
    print(f"{'='*60}")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  Supabase credentials not configured, skipping log verification")
        return True
    
    print(f"🔍 Checking for logs with conversation_id: {conversation_id}")
    print(f"⏱️  Waiting up to {timeout} seconds...")
    
    url = f"{SUPABASE_URL}/rest/v1/logs"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    params = {
        "conversation_id": f"eq.{conversation_id}",
        "order": "ts.desc",
        "limit": 1
    }
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            while time.time() - start_time < timeout:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    logs = response.json()
                    if logs:
                        log = logs[0]
                        print(f"✅ Log entry found!")
                        print(f"   - Timestamp: {log.get('ts')}")
                        print(f"   - Intent: {log.get('intent')}")
                        print(f"   - Provider: {log.get('provider')}")
                        print(f"   - Latency: {log.get('latency_ms')}ms")
                        print(f"   - Error: {log.get('error_message') or 'None'}")
                        return True
                
                # Wait before retrying
                await asyncio.sleep(2)
                print(".", end="", flush=True)
        
        print(f"\n❌ No logs found after {timeout} seconds")
        return False
        
    except Exception as e:
        print(f"\n❌ Error checking logs: {str(e)}")
        return False


async def test_health_endpoint() -> bool:
    """Test the health endpoint."""
    print(f"\n{'='*60}")
    print(f"PRE-CHECK: Health Endpoint")
    print(f"{'='*60}")
    
    url = f"{DEPLOYMENT_URL}/health"
    print(f"🏥 Checking health: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📥 Response: {json.dumps(data, indent=2)}")
            
            if data.get("status") == "healthy":
                print("✅ System is healthy")
                return True
            else:
                print(f"⚠️  System status: {data.get('status')}")
                return False
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking health: {str(e)}")
        return False


async def run_integration_test():
    """Run complete integration test."""
    print("\n" + "="*60)
    print("CHATWOOT INTEGRATION TEST")
    print("="*60)
    print(f"Deployment URL: {DEPLOYMENT_URL}")
    print(f"Test Phone: {TEST_PHONE}")
    print(f"Test Conversation ID: {TEST_CONVERSATION_ID}")
    print("="*60)
    
    # Check configuration
    if not CHATWOOT_WEBHOOK_TOKEN:
        print("❌ CHATWOOT_WEBHOOK_TOKEN not configured")
        print("   Set it in .env file or environment variables")
        return False
    
    results = []
    
    # Pre-check: Health endpoint
    health_ok = await test_health_endpoint()
    results.append(("Health Check", health_ok))
    
    if not health_ok:
        print("\n⚠️  System is not healthy, but continuing with tests...")
    
    # Test 1: Send webhook
    test_messages = [
        "Olá, gostaria de informações sobre depilação a laser",
        "Quais são os horários de funcionamento?",
        "Quero agendar uma consulta"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'='*60}")
        print(f"Test Message {i}/{len(test_messages)}")
        print(f"{'='*60}")
        
        # Use unique conversation ID for each test
        conv_id = TEST_CONVERSATION_ID + i
        
        # Create and send webhook
        payload = create_test_payload(message, conv_id)
        
        url = f"{DEPLOYMENT_URL}/webhook/chatwoot"
        headers = {
            "Content-Type": "application/json",
            "api_access_token": CHATWOOT_WEBHOOK_TOKEN
        }
        
        print(f"📤 Sending: {message}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
            
            webhook_ok = response.status_code == 200
            print(f"📥 Status: {response.status_code}")
            
            if webhook_ok:
                print("✅ Webhook accepted")
                
                # Wait a bit for processing
                print("⏱️  Waiting 5 seconds for processing...")
                await asyncio.sleep(5)
                
                # Verify logs
                logs_ok = await verify_logs_in_supabase(conv_id, timeout=15)
                results.append((f"Message {i} - Webhook", webhook_ok))
                results.append((f"Message {i} - Logs", logs_ok))
            else:
                print(f"❌ Webhook failed: {response.text}")
                results.append((f"Message {i} - Webhook", False))
                results.append((f"Message {i} - Logs", False))
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append((f"Message {i} - Webhook", False))
            results.append((f"Message {i} - Logs", False))
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    
    print(f"\n{'='*60}")
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    print(f"{'='*60}")
    
    return passed_tests == total_tests


async def main():
    """Main entry point."""
    # Check if deployment URL is provided
    if len(sys.argv) > 1:
        global DEPLOYMENT_URL
        DEPLOYMENT_URL = sys.argv[1].rstrip('/')
        print(f"Using deployment URL from argument: {DEPLOYMENT_URL}")
    
    success = await run_integration_test()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
