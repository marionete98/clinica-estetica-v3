#!/usr/bin/env python3
"""
Test all imports in the system to ensure they are correct.
"""

import sys
import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_import(module_name: str, description: str) -> bool:
    """Test importing a module."""
    try:
        __import__(module_name)
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"❌ {description}: {e}")
        traceback.print_exc()
        return False

def main():
    """Test all critical imports."""
    print("🔍 Testing all imports...")
    print("=" * 50)
    
    success_count = 0
    total_count = 0
    
    # Core configuration
    tests = [
        ("config.settings", "Settings configuration"),
        ("config.redis_client", "Redis client"),
        ("config.supabase_client", "Supabase client"),
        ("config.chatwoot_client", "Chatwoot client"),
        
        # Main application
        ("main", "Main FastAPI application"),
        
        # Services
        ("services.agent_orchestrator", "Agent orchestrator"),
        ("services.kb_cache_service", "KB cache service"),
        ("services.message_sender", "Message sender"),
        ("services.alerts", "Alerts service"),
        ("services.metrics", "Metrics service"),
        
        # Agents
        ("agents.supervisor", "Supervisor agent"),
        ("agents.faq", "FAQ agent"),
        ("agents.scheduler", "Scheduler agent"),
        ("agents.intake", "Intake agent"),
        ("agents.escalation", "Escalation agent"),
        ("agents.followup", "Followup agent"),
        
        # Tools
        ("tools.kb_tools_cached", "Cached KB tools"),
        ("tools.scheduler_tools", "Scheduler tools"),
        ("tools.contact_tools", "Contact tools"),
        ("tools.reschedule_tools", "Reschedule tools"),
        ("tools.calendar_api_client", "Calendar API client"),
        
        # Models
        ("models.database", "Database models"),
        ("models.repositories", "Repository namespace"),
        ("models.repositories.contacts", "Contacts repository"),
        ("models.repositories.appointments", "Appointments repository"),
        
        # Routes
        ("routes.webhooks", "Webhooks routes"),
        ("routes.api", "API routes"),
        ("routes.metrics", "Metrics routes"),
        ("routes.dashboard", "Dashboard routes"),
        
        # Jobs
        ("jobs.reminder_job", "Reminder job"),
        ("jobs.feedback_job", "Feedback job"),
        ("jobs.kb_sync_job", "KB sync job"),
        
        # Utils
        ("utils.logger", "Logger utils"),
        ("utils.error_handlers", "Error handlers"),
        ("utils.validators", "Validators"),
        ("utils.graceful_degradation", "Graceful degradation"),
        ("utils.guardrails", "Guardrails"),
        
        # Middleware
        ("middleware.rate_limit", "Rate limit middleware"),
    ]
    
    for module_name, description in tests:
        total_count += 1
        if test_import(module_name, description):
            success_count += 1
    
    print("=" * 50)
    print(f"📊 Results: {success_count}/{total_count} imports successful")
    
    if success_count == total_count:
        print("🎉 All imports are working correctly!")
        return 0
    else:
        print(f"⚠️  {total_count - success_count} imports failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())