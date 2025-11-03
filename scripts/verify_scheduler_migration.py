"""
Verification script for Scheduler Agent AutoGen 0.4 migration.

This script verifies that the scheduler agent has been properly migrated
to AutoGen 0.4 architecture.
"""

import sys
import inspect


def verify_scheduler_migration():
    """Verify scheduler agent migration to AutoGen 0.4."""
    print("=" * 60)
    print("Scheduler Agent AutoGen 0.4 Migration Verification")
    print("=" * 60)
    
    try:
        # Import the scheduler agent
        from agents.scheduler import SchedulerAgent, create_scheduler_agent
        print("✓ Scheduler agent imports successfully")
        
        # Check for AutoGen 0.4 imports
        import agents.scheduler as scheduler_module
        source = inspect.getsource(scheduler_module)
        
        # Verify AutoGen 0.4 imports
        checks = {
            "AssistantAgent import": "from autogen_agentchat.agents import AssistantAgent" in source,
            "TextMessage import": "from autogen_agentchat.messages import TextMessage" in source,
            "OpenAIChatCompletionClient import": "from autogen_ext.models.openai import OpenAIChatCompletionClient" in source,
            "CancellationToken import": "from autogen_core import CancellationToken" in source,
            "No ConversableAgent": "ConversableAgent" not in source or "from autogen import" not in source,
            "No register_function": "register_function" not in source or "from autogen import" not in source,
        }
        
        print("\nImport Checks:")
        for check_name, result in checks.items():
            status = "✓" if result else "✗"
            print(f"  {status} {check_name}")
        
        # Check for required methods
        print("\nMethod Checks:")
        methods = {
            "_create_model_client": hasattr(SchedulerAgent, "_create_model_client"),
            "_create_agent": hasattr(SchedulerAgent, "_create_agent"),
            "_parse_response": hasattr(SchedulerAgent, "_parse_response"),
            "process_scheduling_request": hasattr(SchedulerAgent, "process_scheduling_request"),
            "process_request": hasattr(SchedulerAgent, "process_request"),
            "cleanup": hasattr(SchedulerAgent, "cleanup"),
        }
        
        for method_name, exists in methods.items():
            status = "✓" if exists else "✗"
            print(f"  {status} {method_name}")
        
        # Check if methods are async
        print("\nAsync Method Checks:")
        async_methods = {
            "process_scheduling_request": inspect.iscoroutinefunction(SchedulerAgent.process_scheduling_request),
            "process_request": inspect.iscoroutinefunction(SchedulerAgent.process_request),
            "cleanup": inspect.iscoroutinefunction(SchedulerAgent.cleanup),
        }
        
        for method_name, is_async in async_methods.items():
            status = "✓" if is_async else "✗"
            print(f"  {status} {method_name} is async")
        
        # Summary
        all_checks = list(checks.values()) + list(methods.values()) + list(async_methods.values())
        passed = sum(all_checks)
        total = len(all_checks)
        
        print("\n" + "=" * 60)
        print(f"Migration Status: {passed}/{total} checks passed")
        
        if passed == total:
            print("✓ Scheduler Agent successfully migrated to AutoGen 0.4!")
            return 0
        else:
            print("✗ Some migration checks failed. Please review.")
            return 1
            
    except Exception as e:
        print(f"✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(verify_scheduler_migration())
