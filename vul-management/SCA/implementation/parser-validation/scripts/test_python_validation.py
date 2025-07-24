#!/usr/bin/env python3
"""
Test script for Python parser validation.
"""

import sys
from pathlib import Path

# Add the parser-validation directory to Python path
parser_validation_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parser_validation_dir))

from languages.python.validators.python_parser_validator import PythonParserValidator


def main():
    """Test Python parser validation process."""
    print("🔍 Testing Python parser validation...")
    
    # Initialize validator
    validator = PythonParserValidator()
    print(f"📊 Using parser: {validator.parser_name}")
    
    # Test data directory
    test_data_dir = Path(__file__).parent.parent / "languages/python/test-data/pip-tools"
    
    if not test_data_dir.exists():
        print(f"❌ Test data directory not found: {test_data_dir}")
        print("Run test_pip_tools_extraction.py first to generate test data")
        return
    
    # Run validation
    print(f"\n🧪 Running validation against tests in {test_data_dir}")
    results = validator.run_validation_from_yaml_directory(test_data_dir)
    
    # Print summary
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    failed_tests = total_tests - passed_tests
    
    print(f"\n📊 Validation Results:")
    print(f"   Total tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {failed_tests}")
    print(f"   Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Show some failures for analysis
    if failed_tests > 0:
        print(f"\n❌ Sample failures (showing first 5):")
        failure_count = 0
        for result in results:
            if not result.passed and failure_count < 5:
                print(f"\n{failure_count + 1}. {result.test_id}")
                if result.error:
                    print(f"   Error: {result.error}")
                else:
                    print(f"   Differences:")
                    for diff in result.differences[:3]:  # Show first 3 differences
                        print(f"     - {diff}")
                failure_count += 1
    
    # Generate compatibility report
    print(f"\n📋 Generating compatibility report...")
    try:
        report = validator.generate_compatibility_report("pip-tools")
        
        # Save report to file
        report_file = Path(__file__).parent.parent / "python_parser_compatibility_report.json"
        with open(report_file, 'w') as f:
            f.write(report.to_json())
        
        print(f"✅ Compatibility report saved to: {report_file}")
        print(f"   Overall compatibility score: {report.summary['compatibility_score']}%")
        
        # Show category breakdown
        print(f"\n📈 Category breakdown:")
        for category, stats in report.categories.items():
            pass_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"   {category}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")
        
        # Show recommendations
        if report.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in report.recommendations:
                print(f"   - {rec}")
        
    except Exception as e:
        print(f"❌ Failed to generate compatibility report: {e}")
    
    print("\n🎉 Validation completed!")


if __name__ == "__main__":
    main()