#!/usr/bin/env python3
"""
Verify AutoGen 0.4.x imports are working correctly.
This script checks that all required AutoGen modules can be imported.
"""

import sys
from typing import List, Tuple


def verify_autogen_imports() -> Tuple[bool, List[str]]:
    """
    Verify all AutoGen 0.4.x modules can be imported.
    
    Returns:
        Tuple of (success: bool, errors: List[str])
    """
    errors = []
    
    # Required AutoGen 0.4.x modules
    required_modules = [
        ('autogen_agentchat.agents', 'AssistantAgent'),
        ('autogen_agentchat.messages', 'TextMessage'),
        ('autogen_ext.models.openai', 'OpenAIChatCompletionClient'),
        ('autogen_core', 'CancellationToken'),
    ]
    
    print("🔍 Verifying AutoGen 0.4.x imports...\n")
    
    for module_name, class_name in required_modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            if hasattr(module, class_name):
                print(f"✅ {module_name}.{class_name}")
            else:
                error_msg = f"❌ {module_name} exists but {class_name} not found"
                print(error_msg)
                errors.append(error_msg)
        except ImportError as e:
            error_msg = f"❌ Failed to import {module_name}: {e}"
            print(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"❌ Unexpected error importing {module_name}: {e}"
            print(error_msg)
            errors.append(error_msg)
    
    return len(errors) == 0, errors


def check_package_versions():
    """Check installed AutoGen package versions."""
    print("\n📦 Checking installed AutoGen packages...\n")
    
    try:
        import pkg_resources
        
        autogen_packages = [
            'autogen-agentchat',
            'autogen-core',
            'autogen-ext',
        ]
        
        for package_name in autogen_packages:
            try:
                version = pkg_resources.get_distribution(package_name).version
                print(f"✅ {package_name}: {version}")
            except pkg_resources.DistributionNotFound:
                print(f"❌ {package_name}: NOT INSTALLED")
        
        # Check for old package (should NOT be present)
        try:
            old_version = pkg_resources.get_distribution('pyautogen').version
            print(f"⚠️  pyautogen: {old_version} (OLD PACKAGE - should be removed)")
        except pkg_resources.DistributionNotFound:
            print(f"✅ pyautogen: Not installed (correct - using modular packages)")
            
    except ImportError:
        print("⚠️  pkg_resources not available, skipping version check")


def verify_agent_imports():
    """Verify that agent files can import AutoGen modules."""
    print("\n🤖 Verifying agent file imports...\n")
    
    agent_files = [
        'agents.supervisor',
        'agents.intake',
        'agents.faq',
        'agents.scheduler',
        'agents.escalation',
        'agents.followup',
    ]
    
    errors = []
    
    for agent_module in agent_files:
        try:
            __import__(agent_module)
            print(f"✅ {agent_module}")
        except ImportError as e:
            error_msg = f"❌ Failed to import {agent_module}: {e}"
            print(error_msg)
            errors.append(error_msg)
        except Exception as e:
            error_msg = f"❌ Unexpected error importing {agent_module}: {e}"
            print(error_msg)
            errors.append(error_msg)
    
    return len(errors) == 0, errors


def main():
    """Main verification function."""
    print("=" * 70)
    print("AutoGen 0.4.x Import Verification")
    print("=" * 70)
    
    # Step 1: Check package versions
    check_package_versions()
    
    # Step 2: Verify AutoGen imports
    imports_ok, import_errors = verify_autogen_imports()
    
    # Step 3: Verify agent imports
    agents_ok, agent_errors = verify_agent_imports()
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    if imports_ok and agents_ok:
        print("✅ All AutoGen 0.4.x imports verified successfully!")
        print("✅ All agent files can be imported!")
        print("\n🚀 System is ready for deployment!")
        return 0
    else:
        print("❌ Verification failed!")
        
        if import_errors:
            print("\n❌ AutoGen Import Errors:")
            for error in import_errors:
                print(f"   - {error}")
        
        if agent_errors:
            print("\n❌ Agent Import Errors:")
            for error in agent_errors:
                print(f"   - {error}")
        
        print("\n🔧 Fix Required:")
        print("   1. Ensure requirements.txt has:")
        print("      - autogen-agentchat==0.4.0")
        print("      - autogen-core==0.4.0")
        print("      - autogen-ext[openai]==0.4.0")
        print("   2. Run: pip install -r requirements.txt")
        print("   3. Rebuild Docker image if deploying to production")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())

