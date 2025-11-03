#!/usr/bin/env python3
"""
Deployment verification script for Railway.

This script verifies that a Railway deployment is healthy and all
components are functioning correctly.

Usage:
    python scripts/verify_deployment.py https://your-app.railway.app
    
Requirements: 9.4
"""

import sys
import time
import requests
from typing import Dict, List, Tuple
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def verify_health(base_url: str) -> Tuple[bool, Dict]:
    """
    Verify the health endpoint.
    
    Args:
        base_url: Base URL of the deployment
        
    Returns:
        Tuple of (success, response_data)
    """
    print_header("Verifying Health Endpoint")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code != 200:
            print_error(f"Health check returned status {response.status_code}")
            return False, {}
        
        data = response.json()
        
        # Check overall status
        status = data.get("status")
        if status == "healthy":
            print_success(f"Overall status: {status}")
        else:
            print_warning(f"Overall status: {status}")
        
        # Check individual components
        checks = data.get("checks", {})
        details = data.get("details", {})
        
        all_healthy = True
        for component, is_healthy in checks.items():
            detail = details.get(component, "")
            if is_healthy:
                print_success(f"{component}: {detail}")
            else:
                print_error(f"{component}: {detail}")
                all_healthy = False
        
        # Display version and timestamp
        print_info(f"Version: {data.get('version', 'unknown')}")
        print_info(f"Timestamp: {data.get('timestamp', 'unknown')}")
        
        return all_healthy, data
        
    except requests.exceptions.Timeout:
        print_error("Health check timed out (> 10 seconds)")
        return False, {}
    except requests.exceptions.RequestException as e:
        print_error(f"Health check failed: {e}")
        return False, {}
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False, {}


def verify_scheduler(base_url: str) -> Tuple[bool, Dict]:
    """
    Verify the scheduler status.
    
    Args:
        base_url: Base URL of the deployment
        
    Returns:
        Tuple of (success, response_data)
    """
    print_header("Verifying Scheduler Status")
    
    try:
        response = requests.get(f"{base_url}/scheduler/status", timeout=10)
        
        if response.status_code != 200:
            print_error(f"Scheduler status returned {response.status_code}")
            return False, {}
        
        data = response.json()
        
        status = data.get("status")
        if status == "running":
            print_success(f"Scheduler status: {status}")
        else:
            print_error(f"Scheduler status: {status}")
            return False, data
        
        # Check jobs
        jobs = data.get("jobs", [])
        job_count = data.get("job_count", 0)
        
        if job_count < 3:
            print_warning(f"Expected 3 jobs, found {job_count}")
        else:
            print_success(f"Found {job_count} scheduled jobs")
        
        # List jobs
        for job in jobs:
            job_id = job.get("id")
            job_name = job.get("name")
            next_run = job.get("next_run", "Not scheduled")
            print_info(f"  - {job_id}: {job_name}")
            print_info(f"    Next run: {next_run}")
        
        return True, data
        
    except Exception as e:
        print_error(f"Scheduler check failed: {e}")
        return False, {}


def verify_metrics(base_url: str) -> Tuple[bool, Dict]:
    """
    Verify the metrics endpoint.
    
    Args:
        base_url: Base URL of the deployment
        
    Returns:
        Tuple of (success, response_data)
    """
    print_header("Verifying Metrics Endpoint")
    
    try:
        response = requests.get(f"{base_url}/metrics", timeout=10)
        
        if response.status_code != 200:
            print_error(f"Metrics endpoint returned {response.status_code}")
            return False, {}
        
        data = response.json()
        
        print_success("Metrics endpoint is accessible")
        
        # Display metrics (may be null for new deployment)
        p95 = data.get("p95_latency_ms")
        handover = data.get("handover_rate_percent")
        conversion = data.get("conversion_rate_percent")
        cost = data.get("cost_per_conversation")
        total = data.get("total_conversations", 0)
        
        print_info(f"Total conversations: {total}")
        
        if p95 is not None:
            if p95 <= 7000:
                print_success(f"P95 latency: {p95}ms (target: ≤7000ms)")
            else:
                print_warning(f"P95 latency: {p95}ms (target: ≤7000ms)")
        else:
            print_info("P95 latency: No data yet")
        
        if handover is not None:
            if handover < 30:
                print_success(f"Handover rate: {handover}% (target: <30%)")
            else:
                print_warning(f"Handover rate: {handover}% (target: <30%)")
        else:
            print_info("Handover rate: No data yet")
        
        if conversion is not None:
            if conversion > 70:
                print_success(f"Conversion rate: {conversion}% (target: >70%)")
            else:
                print_warning(f"Conversion rate: {conversion}% (target: >70%)")
        else:
            print_info("Conversion rate: No data yet")
        
        if cost is not None:
            if cost < 0.50:
                print_success(f"Cost per conversation: R${cost:.4f} (target: <R$0.50)")
            else:
                print_warning(f"Cost per conversation: R${cost:.4f} (target: <R$0.50)")
        else:
            print_info("Cost per conversation: No data yet")
        
        return True, data
        
    except Exception as e:
        print_error(f"Metrics check failed: {e}")
        return False, {}


def verify_chat(base_url: str) -> Tuple[bool, Dict]:
    """
    Verify the chat endpoint with a test message.
    
    Args:
        base_url: Base URL of the deployment
        
    Returns:
        Tuple of (success, response_data)
    """
    print_header("Verifying Chat Endpoint")
    
    try:
        payload = {
            "phone": "+5594991398585",
            "message": "Olá, gostaria de informações sobre a clínica"
        }
        
        print_info("Sending test message...")
        
        response = requests.post(
            f"{base_url}/chat",
            json=payload,
            timeout=30  # Chat may take longer
        )
        
        if response.status_code != 200:
            print_error(f"Chat endpoint returned {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
            return False, {}
        
        data = response.json()
        
        print_success("Chat endpoint is functional")
        
        # Display response details
        intent = data.get("intent", "unknown")
        agent = data.get("agent", "unknown")
        confidence = data.get("confidence", "unknown")
        response_text = data.get("response", "")
        
        print_info(f"Intent detected: {intent}")
        print_info(f"Agent used: {agent}")
        print_info(f"Confidence: {confidence}")
        print_info(f"Response preview: {response_text[:100]}...")
        
        return True, data
        
    except requests.exceptions.Timeout:
        print_error("Chat request timed out (> 30 seconds)")
        print_warning("This may indicate LLM provider issues")
        return False, {}
    except Exception as e:
        print_error(f"Chat check failed: {e}")
        return False, {}


def verify_dashboard(base_url: str) -> bool:
    """
    Verify the dashboard is accessible.
    
    Args:
        base_url: Base URL of the deployment
        
    Returns:
        True if accessible, False otherwise
    """
    print_header("Verifying Dashboard")
    
    try:
        response = requests.get(f"{base_url}/dashboard", timeout=10)
        
        if response.status_code != 200:
            print_error(f"Dashboard returned {response.status_code}")
            return False
        
        print_success("Dashboard is accessible")
        print_info(f"URL: {base_url}/dashboard")
        
        return True
        
    except Exception as e:
        print_error(f"Dashboard check failed: {e}")
        return False


def verify_root(base_url: str) -> bool:
    """
    Verify the root endpoint.
    
    Args:
        base_url: Base URL of the deployment
        
    Returns:
        True if accessible, False otherwise
    """
    print_header("Verifying Root Endpoint")
    
    try:
        response = requests.get(base_url, timeout=10)
        
        if response.status_code != 200:
            print_error(f"Root endpoint returned {response.status_code}")
            return False
        
        data = response.json()
        
        print_success("Root endpoint is accessible")
        print_info(f"Service: {data.get('message', 'unknown')}")
        print_info(f"Version: {data.get('version', 'unknown')}")
        
        return True
        
    except Exception as e:
        print_error(f"Root endpoint check failed: {e}")
        return False


def main():
    """Main verification function."""
    if len(sys.argv) < 2:
        print(f"{Colors.RED}Usage: python scripts/verify_deployment.py <base_url>{Colors.RESET}")
        print(f"{Colors.YELLOW}Example: python scripts/verify_deployment.py https://your-app.railway.app{Colors.RESET}")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print(f"\n{Colors.BOLD}Railway Deployment Verification{Colors.RESET}")
    print(f"{Colors.BOLD}Clínica Luana Multi-Agent System{Colors.RESET}")
    print(f"\n{Colors.BOLD}Target URL:{Colors.RESET} {base_url}\n")
    
    results = {}
    
    # Run all verifications
    results["root"] = verify_root(base_url)
    results["health"], health_data = verify_health(base_url)
    results["scheduler"], scheduler_data = verify_scheduler(base_url)
    results["metrics"], metrics_data = verify_metrics(base_url)
    results["chat"], chat_data = verify_chat(base_url)
    results["dashboard"] = verify_dashboard(base_url)
    
    # Summary
    print_header("Verification Summary")
    
    for check, passed in results.items():
        if passed:
            print_success(f"{check.capitalize()}: PASSED")
        else:
            print_error(f"{check.capitalize()}: FAILED")
    
    # Overall result
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All verifications passed!{Colors.RESET}")
        print(f"{Colors.GREEN}Deployment is healthy and ready for use.{Colors.RESET}\n")
        
        print(f"{Colors.BOLD}Next Steps:{Colors.RESET}")
        print("1. Configure Chatwoot webhook")
        print("2. Test webhook integration")
        print("3. Monitor logs for first hour")
        print("4. Review metrics after 24 hours")
        print(f"\n{Colors.BOLD}Useful URLs:{Colors.RESET}")
        print(f"  Dashboard: {base_url}/dashboard")
        print(f"  Health: {base_url}/health")
        print(f"  Metrics: {base_url}/metrics")
        print(f"  Docs: {base_url}/docs\n")
        
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some verifications failed{Colors.RESET}")
        print(f"{Colors.RED}Please review the errors above and fix before proceeding.{Colors.RESET}\n")
        
        print(f"{Colors.BOLD}Troubleshooting:{Colors.RESET}")
        print("1. Check Railway deployment logs")
        print("2. Verify all environment variables are set")
        print("3. Check external service status (Supabase, Redis, Chatwoot)")
        print("4. Review health check details above")
        print("5. Consult docs/RAILWAY_DEPLOYMENT_GUIDE.md\n")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
