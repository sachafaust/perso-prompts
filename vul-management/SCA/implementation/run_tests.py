#!/usr/bin/env python
"""
Test runner script for the AI-powered SCA scanner.
Runs tests with coverage reporting and performance benchmarks.
"""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run the complete test suite."""
    
    print("🧪 Running AI-Powered SCA Scanner Tests")
    print("=" * 50)
    
    # Base pytest command
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker validation
    ]
    
    # Add coverage if requested
    if "--coverage" in sys.argv:
        pytest_cmd.extend([
            "--cov=sca_ai_scanner",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-fail-under=85"  # Require 85% coverage minimum
        ])
        print("📊 Running with coverage reporting (target: 85%+)")
    
    # Add specific test selection
    if "--unit" in sys.argv:
        pytest_cmd.append("tests/unit/")
        print("🔧 Running unit tests only")
    elif "--integration" in sys.argv:
        pytest_cmd.append("tests/integration/")
        print("🔗 Running integration tests only")
    elif "--performance" in sys.argv:
        pytest_cmd.extend(["-m", "performance"])
        print("⚡ Running performance tests only")
    else:
        pytest_cmd.append("tests/")
        print("🔄 Running all tests")
    
    # Add quick mode (fail fast)
    if "--quick" in sys.argv:
        pytest_cmd.extend(["--maxfail=1", "-x"])
        print("🏃 Quick mode: stopping on first failure")
    
    # Run the tests
    print("=" * 50)
    print(f"Executing: {' '.join(pytest_cmd)}")
    print("=" * 50 + "\n")
    
    result = subprocess.run(pytest_cmd)
    
    # Print results summary
    print("\n" + "=" * 50)
    if result.returncode == 0:
        print("✅ All tests passed!")
        
        if "--coverage" in sys.argv:
            print("📄 Coverage report saved to htmlcov/index.html")
    else:
        print("❌ Tests failed!")
        sys.exit(1)
    
    return result.returncode


def run_type_checking():
    """Run mypy type checking."""
    
    print("\n🔍 Running type checking with mypy")
    print("=" * 50)
    
    mypy_cmd = [
        sys.executable, "-m", "mypy",
        "src/sca_ai_scanner",
        "--ignore-missing-imports",
        "--strict"
    ]
    
    result = subprocess.run(mypy_cmd)
    
    if result.returncode == 0:
        print("✅ Type checking passed!")
    else:
        print("❌ Type checking failed!")
    
    return result.returncode


def run_linting():
    """Run code linting with ruff."""
    
    print("\n🧹 Running code linting with ruff")
    print("=" * 50)
    
    ruff_cmd = [
        sys.executable, "-m", "ruff",
        "check",
        "src/sca_ai_scanner",
        "tests/"
    ]
    
    result = subprocess.run(ruff_cmd)
    
    if result.returncode == 0:
        print("✅ Linting passed!")
    else:
        print("❌ Linting failed!")
        print("💡 Run 'ruff check --fix' to auto-fix issues")
    
    return result.returncode


def main():
    """Main test runner."""
    
    print("""
╔══════════════════════════════════════════════════════╗
║      AI-Powered SCA Scanner - Test Suite             ║
╚══════════════════════════════════════════════════════╝

Usage:
  python run_tests.py                 # Run all tests
  python run_tests.py --unit          # Run unit tests only
  python run_tests.py --integration   # Run integration tests only
  python run_tests.py --performance   # Run performance tests only
  python run_tests.py --coverage      # Run with coverage reporting
  python run_tests.py --quick         # Stop on first failure
  python run_tests.py --all           # Run tests + type checking + linting
""")
    
    if "--help" in sys.argv or "-h" in sys.argv:
        return 0
    
    # Run all quality checks if requested
    if "--all" in sys.argv:
        lint_result = run_linting()
        type_result = run_type_checking()
        test_result = run_tests()
        
        print("\n" + "=" * 50)
        print("📊 Quality Check Summary:")
        print(f"  Linting: {'✅ Passed' if lint_result == 0 else '❌ Failed'}")
        print(f"  Type Checking: {'✅ Passed' if type_result == 0 else '❌ Failed'}")
        print(f"  Tests: {'✅ Passed' if test_result == 0 else '❌ Failed'}")
        
        if any([lint_result, type_result, test_result]):
            print("\n❌ Quality checks failed!")
            return 1
        else:
            print("\n✅ All quality checks passed!")
            return 0
    
    # Just run tests
    return run_tests()


if __name__ == "__main__":
    sys.exit(main())