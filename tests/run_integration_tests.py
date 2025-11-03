"""
Integration Test Runner for Clínica Luana Multi-Agent System.

This script runs all integration tests and generates a comprehensive report.

Usage:
    python tests/run_integration_tests.py
    
Or run specific test suites:
    pytest tests/test_e2e.py -v
    pytest tests/test_performance.py -v
    pytest tests/test_error_scenarios.py -v
"""

import sys
import subprocess
from pathlib import Path


def run_test_suite(test_file: str, description: str) -> bool:
    """
    Run a test suite and return success status.
    
    Args:
        test_file: Path to test file
        description: Description of test suite
        
    Returns:
        True if tests passed, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"File: {test_file}")
    print(f"{'='*70}\n")
    
    try:
        result = subprocess.run(
            ["pytest", test_file, "-v", "-s", "--tb=short"],
            capture_output=False,
            text=True
        )
        
        success = result.returncode == 0
        
        if success:
            print(f"\n✓ {description} - PASSED")
        else:
            print(f"\n✗ {description} - FAILED")
        
        return success
        
    except Exception as e:
        print(f"\n✗ Error running {description}: {e}")
        return False


def main():
    """Run all integration test suites."""
    print("\n" + "="*70)
    print("CLÍNICA LUANA - INTEGRATION TEST SUITE")
    print("="*70)
    
    test_suites = [
        ("tests/test_e2e.py", "End-to-End Integration Tests"),
        ("tests/test_performance.py", "Performance Validation Tests"),
        ("tests/test_error_scenarios.py", "Error Scenario Tests"),
    ]
    
    results = {}
    
    for test_file, description in test_suites:
        # Check if file exists
        if not Path(test_file).exists():
            print(f"\n⚠ Warning: {test_file} not found, skipping...")
            results[description] = None
            continue
        
        success = run_test_suite(test_file, description)
        results[description] = success
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for description, success in results.items():
        if success is None:
            status = "⚠ SKIPPED"
        elif success:
            status = "✓ PASSED"
        else:
            status = "✗ FAILED"
        
        print(f"{status:12} - {description}")
    
    # Overall result
    passed = sum(1 for s in results.values() if s is True)
    failed = sum(1 for s in results.values() if s is False)
    skipped = sum(1 for s in results.values() if s is None)
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed > 0:
        print("\n⚠ Some tests failed. Please review the output above.")
        sys.exit(1)
    else:
        print("\n✓ All integration tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
