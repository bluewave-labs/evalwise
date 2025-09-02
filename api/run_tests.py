#!/usr/bin/env python3
"""
Test runner for EvalWise API
Runs different categories of tests and provides summaries.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Run test categories"""
    print("EvalWise API Test Runner")
    print("=" * 60)
    
    # Test categories that are known to work
    test_commands = [
        (
            "python -m pytest tests/test_utils.py::TestLogging -v --tb=short",
            "Logging System Tests"
        ),
        (
            "python -m pytest tests/test_utils.py::TestErrorHandling -v --tb=short", 
            "Error Handling Tests"
        ),
        (
            "python -m pytest tests/test_utils.py::TestConfiguration -v --tb=short",
            "Configuration Tests"
        ),
        (
            "python -m pytest tests/test_auth.py::TestSecurityUtils -v --tb=short",
            "Security Utilities Tests"
        ),
        (
            "python -m pytest tests/test_utils.py::TestDatabaseIntegration -v --tb=short",
            "Database Integration Tests"
        ),
    ]
    
    results = []
    for cmd, description in test_commands:
        success = run_command(cmd, description)
        results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{description:<40} {status}")
    
    print(f"\nOverall: {passed}/{total} test categories passed")
    
    if passed == total:
        print("\n🎉 All working test categories are passing!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test categories failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())