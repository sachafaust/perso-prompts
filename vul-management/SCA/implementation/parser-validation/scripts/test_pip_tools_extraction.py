#!/usr/bin/env python3
"""
Test script for pip-tools test extraction.
"""

import sys
from pathlib import Path

# Add the parser-validation directory to Python path
parser_validation_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parser_validation_dir))

# Now we can import using absolute imports
from languages.python.sources.pip_tools import PipToolsTestExtractor


def main():
    """Test pip-tools extraction process."""
    print("🔍 Testing pip-tools test extraction...")
    
    # Create extractor and test with context manager
    with PipToolsTestExtractor() as extractor:
        print(f"📁 Repository cloned to: {extractor.repo_path}")
        
        # Check if test files exist
        test_files = extractor.get_test_files()
        print(f"📋 Found {len(test_files)} test files:")
        for test_file in test_files:
            print(f"  - {test_file.name}")
        
        # Extract a few test cases for verification
        print("\n🔬 Extracting test cases...")
        test_cases = extractor.extract_tests()
        
        print(f"✅ Extracted {len(test_cases)} test cases")
        
        # Show sample test cases
        if test_cases:
            print("\n📝 Sample test cases:")
            for i, test_case in enumerate(test_cases[:3]):  # Show first 3
                print(f"\n{i+1}. {test_case.id}")
                print(f"   Category: {test_case.category.value}")
                print(f"   Input: {test_case.input.content}")
                print(f"   Expected packages: {len(test_case.expected.packages)}")
                if test_case.expected.packages:
                    pkg = test_case.expected.packages[0]
                    print(f"   First package: {pkg.name} {pkg.version_constraint}")
                print(f"   Difficulty: {test_case.metadata.difficulty.value}")
        
        # Save to YAML files
        output_dir = Path(__file__).parent.parent / "languages/python/test-data/pip-tools"
        print(f"\n💾 Saving tests to {output_dir}")
        extractor.save_tests_to_yaml(output_dir, test_cases)
        
        print("\n🎉 Extraction completed successfully!")


if __name__ == "__main__":
    main()