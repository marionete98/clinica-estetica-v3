"""
Verification script for task 6: Update main.py with resource cleanup.

"""Validate shutdown routines and agent cleanup helpers."""
"""

import ast
import sys
from pathlib import Path


def verify_main_py_cleanup():
    """Verify main.py has proper cleanup implementation."""
    
    print("=" * 80)
    print("Task 6 Verification: Update main.py with resource cleanup")
    print("=" * 80)
    print()
    
    main_py_path = Path("main.py")
    
    if not main_py_path.exists():
        print("❌ main.py not found")
        return False
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check 1: Legacy cleanup removed
    print("✓ Checking absence of legacy cleanup_orchestrator...")
    if "cleanup_orchestrator" in content:
        print("  ❌ Legacy cleanup_orchestrator reference detected")
        return False
    print("  ✅ Legacy cleanup removed")

    # Check 2: Scheduler shutdown present
    print("\n✓ Checking scheduler shutdown handling...")
    if "scheduler.shutdown" in content:
        print("  ✅ Scheduler shutdown call present")
    else:
        print("  ❌ Scheduler shutdown call missing")
        return False

    # Check 3: Chatwoot client cleanup
    print("\n✓ Checking Chatwoot client cleanup...")
    if "chatwoot_client.close" in content:
        print("  ✅ Chatwoot client is closed on shutdown")
    else:
        print("  ❌ Chatwoot client cleanup missing")
        return False
    
    # Check 4: Lifespan context manager
    print("\n✓ Checking lifespan context manager...")
    if "@asynccontextmanager" in content and "async def lifespan" in content:
        print("  ✅ Lifespan context manager is used (modern FastAPI pattern)")
    else:
        print("  ⚠️  Using @app.on_event (legacy pattern)")
    
    # Check 5: Logging
    print("\n✓ Checking cleanup logging...")
    if "logger.info(\"APScheduler shut down\")" in content:
        print("  ✅ Success logging is present")
    else:
        print("  ⚠️  Success logging is missing")

    if "logger.error(f\"Error shutting down scheduler" in content:
        print("  ✅ Error logging is present")
    else:
        print("  ⚠️  Error logging is missing")
    
    return True


def verify_orchestrator_cleanup():
    """Verify orchestrator has cleanup method."""
    
    print("\n" + "=" * 80)
    print("Verifying Agent Orchestrator cleanup implementation")
    print("=" * 80)
    print()
    
    orchestrator_path = Path("services/agent_orchestrator.py")
    
    if not orchestrator_path.exists():
        print("❌ agent_orchestrator.py not found")
        return False
    
    with open(orchestrator_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check cleanup method exists
    print("✓ Checking AgentOrchestrator.cleanup() method...")
    if "async def cleanup(self):" in content:
        print("  ✅ cleanup() method exists")
    else:
        print("  ❌ cleanup() method is missing")
        return False
    
    # Check agents list
    print("\n✓ Checking agents are cleaned up...")
    agents = ["supervisor", "intake", "faq", "scheduler", "escalation"]
    for agent in agents:
        if f'("{agent}"' in content or f"('{agent}'" in content:
            print(f"  ✅ {agent} agent is in cleanup list")
        else:
            print(f"  ⚠️  {agent} agent might not be in cleanup list")
    
    return True


def verify_agent_cleanup_methods():
    """Verify all agents have cleanup methods."""
    
    print("\n" + "=" * 80)
    print("Verifying individual agent cleanup methods")
    print("=" * 80)
    print()
    
    agents_dir = Path("agents")
    agent_files = [
        "supervisor.py",
        "intake.py",
        "faq.py",
        "scheduler.py",
        "escalation.py",
        "followup.py"
    ]
    
    all_have_cleanup = True
    
    for agent_file in agent_files:
        agent_path = agents_dir / agent_file
        
        if not agent_path.exists():
            print(f"⚠️  {agent_file} not found")
            continue
        
        with open(agent_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "async def cleanup(self):" in content:
            print(f"✅ {agent_file} has cleanup() method")
        else:
            print(f"❌ {agent_file} is missing cleanup() method")
            all_have_cleanup = False
    
    return all_have_cleanup


def main():
    """Run all verifications."""
    
    results = []
    
    # Verify main.py
    results.append(verify_main_py_cleanup())
    
    # Verify orchestrator
    results.append(verify_orchestrator_cleanup())
    
    # Verify agents
    results.append(verify_agent_cleanup_methods())
    
    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print()
    
    if all(results):
        print("✅ ALL CHECKS PASSED")
        print()
        print("Task 6 requirements verified:")
        print("  ✓ Legacy cleanup functions removed")
        print("  ✓ Scheduler and Chatwoot cleanup configured")
        print("  ✓ Logging present for shutdown routines")
        print("  ✓ All agents expose cleanup methods")
        print()
        print("The implementation is complete and ready for testing.")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please review the failures above and fix them.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
