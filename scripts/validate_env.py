#!/usr/bin/env python3
"""
Environment variable validation script for Railway deployment.

This script validates that all required environment variables are set
and that API keys are valid before deployment.

Usage:
    python scripts/validate_env.py
    
Requirements: 9.1, 9.2, 9.3, 9.4
"""

import os
import sys
import requests
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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


def check_required_vars() -> Tuple[bool, List[str]]:
    """
    Check that all required environment variables are set.
    
    Returns:
        Tuple of (all_present, missing_vars)
    """
    print_header("Checking Required Environment Variables")
    
    required_vars = [
        "MODEL_PROVIDER",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "REDIS_URL",
        "CHATWOOT_API_URL",
        "CHATWOOT_ACCOUNT_ID",
        "CHATWOOT_API_TOKEN",
        "CHATWOOT_WEBHOOK_TOKEN",
        "CALENDAR_API_URL",
    ]
    
    # Provider-specific requirements
    model_provider = os.getenv("MODEL_PROVIDER", "").lower()
    
    if model_provider == "xai":
        required_vars.append("XAI_API_KEY")
    elif model_provider == "gemini":
        required_vars.append("GEMINI_API_KEY")
    else:
        print_error(f"Invalid MODEL_PROVIDER: {model_provider}")
        print_error("Must be 'xai' or 'gemini'")
        return False, ["MODEL_PROVIDER"]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print_error(f"{var} is not set")
            missing_vars.append(var)
        else:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var or "PASSWORD" in var:
                display_value = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display_value = value
            print_success(f"{var} = {display_value}")
    
    if missing_vars:
        print_error(f"\n{len(missing_vars)} required variable(s) missing")
        return False, missing_vars
    else:
        print_success(f"\nAll {len(required_vars)} required variables are set")
        return True, []


def validate_xai_key() -> bool:
    """
    Validate xAI API key by making a test request.
    
    Returns:
        True if valid, False otherwise
    """
    print_header("Validating xAI API Key")
    
    api_key = os.getenv("XAI_API_KEY")
    model = os.getenv("XAI_MODEL", "grok-4-reasoning")
    base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
    
    if not api_key:
        print_warning("XAI_API_KEY not set, skipping validation")
        return True
    
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print_success(f"xAI API key is valid (model: {model})")
            return True
        else:
            print_error(f"xAI API key validation failed: {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_error(f"Error validating xAI API key: {e}")
        return False


def validate_gemini_key() -> bool:
    """
    Validate Gemini API key by making a test request.
    
    Returns:
        True if valid, False otherwise
    """
    print_header("Validating Gemini API Key")
    
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    if not api_key:
        print_warning("GEMINI_API_KEY not set, skipping validation")
        return True
    
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": "test"}]}]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print_success(f"Gemini API key is valid (model: {model})")
            return True
        else:
            print_error(f"Gemini API key validation failed: {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_error(f"Error validating Gemini API key: {e}")
        return False


def validate_supabase() -> bool:
    """
    Validate Supabase connection.
    
    Returns:
        True if valid, False otherwise
    """
    print_header("Validating Supabase Connection")
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print_error("SUPABASE_URL or SUPABASE_KEY not set")
        return False
    
    try:
        response = requests.get(
            f"{url}/rest/v1/contacts?select=id&limit=1",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print_success("Supabase connection is valid")
            return True
        else:
            print_error(f"Supabase connection failed: {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_error(f"Error validating Supabase connection: {e}")
        return False


def validate_chatwoot() -> bool:
    """
    Validate Chatwoot API connection.
    
    Returns:
        True if valid, False otherwise
    """
    print_header("Validating Chatwoot API Connection")
    
    api_url = os.getenv("CHATWOOT_API_URL")
    account_id = os.getenv("CHATWOOT_ACCOUNT_ID")
    api_token = os.getenv("CHATWOOT_API_TOKEN")
    
    if not all([api_url, account_id, api_token]):
        print_error("Chatwoot configuration incomplete")
        return False
    
    try:
        response = requests.get(
            f"{api_url}/api/v1/accounts/{account_id}/conversations",
            headers={"api_access_token": api_token},
            timeout=10
        )
        
        if response.status_code == 200:
            print_success("Chatwoot API connection is valid")
            return True
        else:
            print_error(f"Chatwoot API connection failed: {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_error(f"Error validating Chatwoot API connection: {e}")
        return False


def validate_calendar_api() -> bool:
    """
    Validate Calendar API connection.
    
    Returns:
        True if valid, False otherwise
    """
    print_header("Validating Calendar API Connection")
    
    api_url = os.getenv("CALENDAR_API_URL")
    
    if not api_url:
        print_error("CALENDAR_API_URL not set")
        return False
    
    try:
        # Remove /api suffix if present for health check
        base_url = api_url.replace("/api", "")
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            print_success("Calendar API connection is valid")
            return True
        else:
            print_error(f"Calendar API connection failed: {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print_error(f"Error validating Calendar API connection: {e}")
        return False


def validate_redis() -> bool:
    """
    Validate Redis connection.
    
    Note: This requires redis-py to be installed.
    
    Returns:
        True if valid, False otherwise
    """
    print_header("Validating Redis Connection")
    
    redis_url = os.getenv("REDIS_URL")
    
    if not redis_url:
        print_error("REDIS_URL not set")
        return False
    
    try:
        import redis
        
        # Parse Redis URL
        client = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        client.ping()
        
        print_success("Redis connection is valid")
        return True
        
    except ImportError:
        print_warning("redis-py not installed, skipping Redis validation")
        print_warning("Install with: pip install redis")
        return True
        
    except Exception as e:
        print_error(f"Error validating Redis connection: {e}")
        return False


def check_optional_vars():
    """Check optional environment variables and provide warnings."""
    print_header("Checking Optional Configuration")
    
    optional_vars = {
        "ENV": "production",
        "LOG_LEVEL": "INFO",
        "MAX_TOOL_CALLS_PER_SESSION": "3",
        "RESPONSE_TIMEOUT_SECONDS": "10",
        "MAX_CONTEXT_MESSAGES": "20",
        "BUSINESS_HOURS_START": "08:30",
        "BUSINESS_HOURS_END": "19:00",
        "ALERT_EMAIL": None,
    }
    
    for var, default in optional_vars.items():
        value = os.getenv(var)
        if value:
            print_success(f"{var} = {value}")
        elif default:
            print_warning(f"{var} not set, will use default: {default}")
        else:
            print_warning(f"{var} not set (optional)")


def main():
    """Main validation function."""
    print(f"\n{Colors.BOLD}Railway Deployment Environment Validation{Colors.RESET}")
    print(f"{Colors.BOLD}Clínica Luana Multi-Agent System{Colors.RESET}\n")
    
    results = {}
    
    # Check required variables
    vars_ok, missing = check_required_vars()
    results["required_vars"] = vars_ok
    
    if not vars_ok:
        print_error("\n❌ Validation failed: Missing required variables")
        print_error(f"Missing: {', '.join(missing)}")
        sys.exit(1)
    
    # Validate LLM provider
    model_provider = os.getenv("MODEL_PROVIDER", "").lower()
    
    if model_provider == "xai":
        results["llm"] = validate_xai_key()
    elif model_provider == "gemini":
        results["llm"] = validate_gemini_key()
    
    # Validate external services
    results["supabase"] = validate_supabase()
    results["chatwoot"] = validate_chatwoot()
    results["calendar_api"] = validate_calendar_api()
    results["redis"] = validate_redis()
    
    # Check optional variables
    check_optional_vars()
    
    # Summary
    print_header("Validation Summary")
    
    all_passed = all(results.values())
    
    for service, passed in results.items():
        if passed:
            print_success(f"{service}: PASSED")
        else:
            print_error(f"{service}: FAILED")
    
    if all_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All validations passed!{Colors.RESET}")
        print(f"{Colors.GREEN}System is ready for Railway deployment.{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some validations failed{Colors.RESET}")
        print(f"{Colors.RED}Please fix the issues above before deploying.{Colors.RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
