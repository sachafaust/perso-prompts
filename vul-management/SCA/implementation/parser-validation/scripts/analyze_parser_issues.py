#!/usr/bin/env python3
"""
Analyze specific Python parser issues discovered during validation.
"""

import sys
from pathlib import Path

# Add the parser-validation directory to Python path
parser_validation_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parser_validation_dir))

from languages.python.validators.python_parser_validator import PythonParserValidator

def test_specific_issues():
    """Test specific parser issues with simple examples."""
    print("🔍 Analyzing specific Python parser issues...")
    
    validator = PythonParserValidator()
    
    test_cases = [
        {
            "name": "Basic version constraint",
            "input": "small-fake-a==0.1",
            "expected_version": "==0.1",
            "issue": "Missing == prefix in version"
        },
        {
            "name": "Package with extras",
            "input": "package-a[click]",
            "expected_extras": ["click"],
            "issue": "Extras not parsed"
        },
        {
            "name": "Environment marker",
            "input": "requests>=2.0; python_version >= '3.6'",
            "expected_marker": "python_version >= '3.6'",
            "issue": "Environment markers not parsed"
        },
        {
            "name": "Editable install",
            "input": "-e git+https://github.com/user/repo.git#egg=package",
            "expected_editable": True,
            "expected_url": "git+https://github.com/user/repo.git",
            "issue": "Editable installs not handled"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Input: {test_case['input']}")
        print(f"   Issue: {test_case['issue']}")
        
        # Parse with our validator
        result = validator.parse_dependency_file(test_case['input'], 'requirements.txt')
        
        if result['parse_success'] and result['packages']:
            pkg = result['packages'][0]
            print(f"   Actual result:")
            print(f"     Name: {pkg['name']}")
            print(f"     Version: {pkg['version_constraint']}")
            print(f"     Extras: {pkg['extras']}")
            print(f"     Environment marker: {pkg['environment_marker']}")
            print(f"     Editable: {pkg['editable']}")
            print(f"     URL: {pkg['url']}")
            
            # Check specific issues
            if 'expected_version' in test_case:
                if pkg['version_constraint'] != test_case['expected_version']:
                    print(f"   ❌ VERSION ISSUE: Expected '{test_case['expected_version']}', got '{pkg['version_constraint']}'")
                else:
                    print(f"   ✅ Version constraint correct")
            
            if 'expected_extras' in test_case:
                if set(pkg['extras']) != set(test_case['expected_extras']):
                    print(f"   ❌ EXTRAS ISSUE: Expected {test_case['expected_extras']}, got {pkg['extras']}")
                else:
                    print(f"   ✅ Extras correct")
            
            if 'expected_marker' in test_case:
                if pkg['environment_marker'] != test_case['expected_marker']:
                    print(f"   ❌ MARKER ISSUE: Expected '{test_case['expected_marker']}', got '{pkg['environment_marker']}'")
                else:
                    print(f"   ✅ Environment marker correct")
            
            if 'expected_editable' in test_case:
                if pkg['editable'] != test_case['expected_editable']:
                    print(f"   ❌ EDITABLE ISSUE: Expected {test_case['expected_editable']}, got {pkg['editable']}")
                else:
                    print(f"   ✅ Editable flag correct")
                    
            if 'expected_url' in test_case:
                if pkg['url'] != test_case['expected_url']:
                    print(f"   ❌ URL ISSUE: Expected '{test_case['expected_url']}', got '{pkg['url']}'")
                else:
                    print(f"   ✅ URL correct")
        else:
            print(f"   ❌ PARSING FAILED: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_specific_issues()