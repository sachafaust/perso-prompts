#!/usr/bin/env python3
"""
Test script for Python parser gap analysis - testing uv.lock and poetry.lock transitive dependencies.
"""

import sys
from pathlib import Path

# Add the parser-validation directory to Python path
parser_validation_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parser_validation_dir))

from languages.python.validators.python_parser_validator import PythonParserValidator


def test_directory(validator, test_dir, description):
    """Test a specific directory and return results."""
    print(f"\n🧪 Testing {description}...")
    print(f"📂 Directory: {test_dir}")
    
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return None
    
    # Run validation
    results = validator.run_validation_from_yaml_directory(test_dir)
    
    # Print summary
    total_tests = len(results)
    if total_tests == 0:
        print("⚠️  No test cases found in directory")
        return None
        
    passed_tests = sum(1 for r in results if r.passed)
    failed_tests = total_tests - passed_tests
    
    print(f"📊 Results:")
    print(f"   Total tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {failed_tests}")
    print(f"   Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Show failures for analysis
    if failed_tests > 0:
        print(f"❌ Failures:")
        for result in results:
            if not result.passed:
                print(f"   • {result.test_id}")
                if result.error:
                    print(f"     Error: {result.error}")
                else:
                    print(f"     Differences:")
                    for diff in result.differences[:2]:  # Show first 2 differences
                        print(f"       - {diff}")
    
    return {
        'total': total_tests,
        'passed': passed_tests,
        'failed': failed_tests,
        'results': results
    }


def main():
    """Test Python parser gap analysis."""
    print("🔍 Python Parser Gap Analysis")
    print("Testing uv.lock and poetry.lock transitive dependency detection")
    
    # Initialize validator
    validator = PythonParserValidator()
    print(f"📊 Using parser: {validator.parser_name}")
    
    # Test directories
    base_dir = Path(__file__).parent.parent / "languages/python/test-data"
    
    # Test uv.lock cases
    uv_lock_dir = base_dir / "uv-lock"
    uv_results = test_directory(validator, uv_lock_dir, "uv.lock format parsing")
    
    # Test poetry.lock transitive cases
    poetry_lock_dir = base_dir / "poetry-lock"  
    poetry_results = test_directory(validator, poetry_lock_dir, "poetry.lock transitive dependencies")
    
    # Overall summary
    print("\n" + "="*60)
    print("📈 OVERALL GAP ANALYSIS SUMMARY")
    print("="*60)
    
    total_gap_tests = 0
    total_gap_passed = 0
    
    if uv_results:
        total_gap_tests += uv_results['total']
        total_gap_passed += uv_results['passed']
        print(f"uv.lock support: {uv_results['passed']}/{uv_results['total']} ({(uv_results['passed']/uv_results['total'])*100:.1f}%)")
    
    if poetry_results:
        total_gap_tests += poetry_results['total'] 
        total_gap_passed += poetry_results['passed']
        print(f"poetry.lock transitive: {poetry_results['passed']}/{poetry_results['total']} ({(poetry_results['passed']/poetry_results['total'])*100:.1f}%)")
    
    if total_gap_tests > 0:
        gap_score = (total_gap_passed / total_gap_tests) * 100
        print(f"\n🎯 Gap Analysis Score: {total_gap_passed}/{total_gap_tests} ({gap_score:.1f}%)")
        
        if gap_score < 100:
            print(f"\n💡 Next Steps:")
            print(f"   - {total_gap_tests - total_gap_passed} test case(s) need parser implementation")
            print(f"   - Focus on uv.lock format support and poetry.lock transitive deps")
            print(f"   - Target: 100% compatibility to achieve Semgrep parity")
        else:
            print(f"\n🎉 Perfect score! Ready for parser implementation testing.")
    else:
        print("\n⚠️  No gap analysis test cases found.")
    
    print("\n✅ Gap analysis completed!")


if __name__ == "__main__":
    main()