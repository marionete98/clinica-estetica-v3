"""
Verification script for task 6: Update main.py with resource cleanup.

This script verifies that:
1. cleanup_orchestrator is imported in main.py
2. cleanup_orchestrator is called in the shutdown handler
3. Error handling is in place
4. All agents have cleanup methods
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
    
    # Check 1: Import cleanup_orchestrator
    print("✓ Checking import of cleanup_orchestrator...")
    if "from services.agent_orchestrator import cleanup_orchestrator" in content:
        print("  ✅ cleanup_orchestrator is imported")
    else:
        print("  ❌ cleanup_orchestrator is NOT imported")
        return False
    
    # Check 2: Call cleanup_orchestrator in shutdown
    print("\n✓ Checking cleanup_orchestrator call in shutdown handler...")
    if "await cleanup_orchestrator()" in content:
        print("  ✅ cleanup_orchestrator() is called in shutdown")
    else:
        print("  ❌ cleanup_orchestrator() is NOT called in shutdown")
        return False
    
    # Check 3: Error handling
    print("\n✓ Checking error handling for cleanup...")
    if "try:" in content and "await cleanup_orchestrator()" in content and "except Exception" in content:
        print("  ✅ Error handling is in place")
    else:
        print("  ❌ Error handling is missing")
        return False
    
    # Check 4: Lifespan context manager
    print("\n✓ Checking lifespan context manager...")
    if "@asynccontextmanager" in content and "async def lifespan" in content:
        print("  ✅ Lifespan context manager is used (modern FastAPI pattern)")
    else:
        print("  ⚠️  Using @app.on_event (legacy pattern)")
    
    # Check 5: Logging
    print("\n✓ Checking cleanup logging...")
    if 'logger.info("Agent orchestrator cleaned up")' in content:
        print("  ✅ Success logging is present")
    else:
        print("  ⚠️  Success logging is missing")
    
    if 'logger.error(f"Error cleaning up agent orchestrator:' in content:
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
    
    # Check cleanup_orchestrator function exists
    print("\n✓ Checking cleanup_orchestrator() function...")
    if "async def cleanup_orchestrator():" in content:
        print("  ✅ cleanup_orchestrator() function exists")
    else:
        print("  ❌ cleanup_orchestrator() function is missing")
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
        print("  ✓ cleanup_orchestrator is imported in main.py")
        print("  ✓ Shutdown handler calls cleanup_orchestrator()")
        print("  ✓ Error handling is in place")
        print("  ✓ All agents have cleanup methods")
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
