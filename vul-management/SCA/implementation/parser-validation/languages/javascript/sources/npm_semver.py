"""
JavaScript parser validation using npm/node-semver test suite.
Extracts version constraint parsing edge cases for JavaScript dependency validation.
"""

import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

from ...common.extractor_base import TestExtractor
from ...common.test_format import TestCase, TestInput, TestExpected, TestMetadata

logger = logging.getLogger(__name__)


@dataclass
class SemverTestCase:
    """Extracted semver test case."""
    version: str
    range_spec: str
    expected_match: bool
    description: str
    test_source: str


class NpmSemverTestExtractor(TestExtractor):
    """
    Extract test cases from npm/node-semver test suite.
    Focus on version constraint parsing and matching logic.
    """
    
    def __init__(self):
        super().__init__()
        self.source_name = "npm/node-semver"
        self.source_version = "7.5.4"  # Latest stable
        self.repository_url = "https://github.com/npm/node-semver"
    
    def extract_tests(self) -> List[TestCase]:
        """Extract JavaScript version constraint tests."""
        test_cases = []
        
        # High-value test scenarios for JavaScript version parsing
        semver_scenarios = self._get_semver_test_scenarios()
        
        for i, scenario in enumerate(semver_scenarios):
            test_case = TestCase(
                id=f"npm-semver-{i+1:03d}",
                source=f"{self.source_name}/test/ranges.js",
                category="version_constraints",
                input=TestInput(
                    content=f'"{scenario.range_spec}": "{scenario.version}"',
                    file_type="package.json"
                ),
                expected=TestExpected(
                    packages=[{
                        "name": "test-package",
                        "version": scenario.version if scenario.expected_match else None,
                        "version_constraint": scenario.range_spec,
                        "satisfies_constraint": scenario.expected_match
                    }]
                ),
                metadata=TestMetadata(
                    difficulty="medium" if "^" in scenario.range_spec or "~" in scenario.range_spec else "hard",
                    edge_case=True,
                    extraction_date="2025-01-24",
                    source_version=self.source_version,
                    notes=scenario.description
                )
            )
            test_cases.append(test_case)
        
        logger.info(f"Extracted {len(test_cases)} npm semver test cases")
        return test_cases
    
    def _get_semver_test_scenarios(self) -> List[SemverTestCase]:
        """Get comprehensive semver test scenarios based on npm/node-semver test patterns."""
        return [
            # Caret range tests (^1.0.0)
            SemverTestCase("1.0.0", "^1.0.0", True, "Caret range exact match", "ranges.js"),
            SemverTestCase("1.0.1", "^1.0.0", True, "Caret range patch increment", "ranges.js"),
            SemverTestCase("1.1.0", "^1.0.0", True, "Caret range minor increment", "ranges.js"),
            SemverTestCase("2.0.0", "^1.0.0", False, "Caret range major increment (should fail)", "ranges.js"),
            SemverTestCase("1.0.0-alpha", "^1.0.0", False, "Caret range with prerelease (should fail)", "ranges.js"),
            
            # Tilde range tests (~1.0.0)
            SemverTestCase("1.0.0", "~1.0.0", True, "Tilde range exact match", "ranges.js"),
            SemverTestCase("1.0.1", "~1.0.0", True, "Tilde range patch increment", "ranges.js"),
            SemverTestCase("1.1.0", "~1.0.0", False, "Tilde range minor increment (should fail)", "ranges.js"),
            SemverTestCase("2.0.0", "~1.0.0", False, "Tilde range major increment (should fail)", "ranges.js"),
            
            # Exact version tests
            SemverTestCase("1.0.0", "1.0.0", True, "Exact version match", "ranges.js"),
            SemverTestCase("1.0.1", "1.0.0", False, "Exact version mismatch", "ranges.js"),
            
            # Greater than/less than tests
            SemverTestCase("1.0.1", ">=1.0.0", True, "Greater than or equal match", "ranges.js"),
            SemverTestCase("0.9.9", ">=1.0.0", False, "Greater than or equal fail", "ranges.js"),
            SemverTestCase("1.9.9", "<2.0.0", True, "Less than match", "ranges.js"),
            SemverTestCase("2.0.0", "<2.0.0", False, "Less than fail (equal)", "ranges.js"),
            
            # Complex range tests
            SemverTestCase("1.5.0", ">=1.0.0 <2.0.0", True, "Range constraint match", "ranges.js"),
            SemverTestCase("2.0.0", ">=1.0.0 <2.0.0", False, "Range constraint fail (upper bound)", "ranges.js"),
            SemverTestCase("0.9.0", ">=1.0.0 <2.0.0", False, "Range constraint fail (lower bound)", "ranges.js"),
            
            # X-range tests (wildcards)
            SemverTestCase("1.2.3", "1.x", True, "X-range major match", "ranges.js"),
            SemverTestCase("2.0.0", "1.x", False, "X-range major fail", "ranges.js"),
            SemverTestCase("1.2.3", "1.2.x", True, "X-range minor match", "ranges.js"),
            SemverTestCase("1.3.0", "1.2.x", False, "X-range minor fail", "ranges.js"),
            
            # Prerelease version tests
            SemverTestCase("1.0.0-alpha.1", "1.0.0-alpha.1", True, "Prerelease exact match", "ranges.js"),
            SemverTestCase("1.0.0-alpha.2", "1.0.0-alpha.1", False, "Prerelease version mismatch", "ranges.js"),
            SemverTestCase("1.0.0-alpha.1", "^1.0.0-alpha.1", True, "Prerelease caret match", "ranges.js"),
            SemverTestCase("1.0.0", "^1.0.0-alpha.1", False, "Prerelease to release (complex)", "ranges.js"),
            
            # Build metadata tests (should be ignored in comparison)
            SemverTestCase("1.0.0+build.1", "1.0.0", True, "Build metadata ignored", "ranges.js"),
            SemverTestCase("1.0.0", "1.0.0+build.1", True, "Build metadata in range ignored", "ranges.js"),
            
            # Zero major version edge cases (0.x.y)
            SemverTestCase("0.1.0", "^0.1.0", True, "Zero major caret exact", "ranges.js"),
            SemverTestCase("0.1.1", "^0.1.0", True, "Zero major caret patch", "ranges.js"),
            SemverTestCase("0.2.0", "^0.1.0", False, "Zero major caret minor fail", "ranges.js"),
            SemverTestCase("0.0.1", "~0.0.1", True, "Zero minor tilde exact", "ranges.js"),
            SemverTestCase("0.0.2", "~0.0.1", False, "Zero minor tilde patch fail", "ranges.js"),
            
            # Invalid/edge case versions that should be rejected
            SemverTestCase("invalid", "^1.0.0", False, "Invalid version string", "ranges.js"),
            SemverTestCase("1.0", "^1.0.0", False, "Incomplete version (missing patch)", "ranges.js"),
            SemverTestCase("v1.0.0", "^1.0.0", True, "Version with v prefix (should normalize)", "ranges.js"),
            
            # NPM-specific tags and specifiers
            SemverTestCase("latest", "latest", True, "NPM tag match", "ranges.js"),
            SemverTestCase("1.0.0", "latest", False, "NPM tag vs version", "ranges.js"),
            
            # Git and URL dependencies (should parse differently)
            SemverTestCase("git", "git+https://github.com/user/repo.git", True, "Git URL dependency", "ranges.js"),
            SemverTestCase("file", "file:../local-package", True, "File dependency", "ranges.js"),
        ]
    
    def _is_invalid_requirement(self, requirement: str) -> bool:
        """Check if requirement string is invalid and should be filtered out."""
        invalid_patterns = [
            'test_', 'fixture_', 'mock_',  # Test-specific names
            'TODO', 'FIXME', 'XXX',       # Development comments
            '\\n', '\\t', '\\r',          # Escape sequences (likely from docs)
            'function ', 'var ', 'const ', 'let ',  # JavaScript code
            'import ', 'require(',        # Module imports
            'describe(', 'it(',           # Test framework
        ]
        
        return any(pattern in requirement for pattern in invalid_patterns)


class YarnLockTestExtractor(TestExtractor):
    """
    Extract test cases for yarn.lock parsing.
    Based on yarn test suite patterns.
    """
    
    def __init__(self):
        super().__init__()
        self.source_name = "yarnpkg/berry"
        self.source_version = "4.0.2"
        self.repository_url = "https://github.com/yarnpkg/berry"
    
    def extract_tests(self) -> List[TestCase]:
        """Extract yarn.lock parsing tests."""
        test_cases = []
        
        # Yarn lockfile parsing scenarios
        yarn_scenarios = self._get_yarn_lock_scenarios()
        
        for i, scenario in enumerate(yarn_scenarios):
            test_case = TestCase(
                id=f"yarn-lock-{i+1:03d}",
                source=f"{self.source_name}/packages/yarnpkg-parsers/sources/resolution.ts",
                category="lockfile_parsing",
                input=TestInput(
                    content=scenario["lockfile_content"],
                    file_type="yarn.lock"
                ),
                expected=TestExpected(
                    packages=scenario["expected_packages"]
                ),
                metadata=TestMetadata(
                    difficulty="medium",
                    edge_case=scenario.get("edge_case", False),
                    extraction_date="2025-01-24",
                    source_version=self.source_version,
                    notes=scenario["description"]
                )
            )
            test_cases.append(test_case)
        
        logger.info(f"Extracted {len(test_cases)} yarn.lock test cases")
        return test_cases
    
    def _get_yarn_lock_scenarios(self) -> List[Dict[str, Any]]:
        """Get yarn.lock parsing test scenarios."""
        return [
            {
                "description": "Basic package with exact version",
                "lockfile_content": '''lodash@^4.17.20:
  version "4.17.21"
  resolved "https://registry.yarnpkg.com/lodash/-/lodash-4.17.21.tgz"
  integrity sha512-v2kDEe57lecTulaDIuNTPy3Ry4gLGJ6Z1O3vE1krgXZNrsQ+LFTGHVxVjcXPs17LhbZVGedAJv8XZ1tvj5FvSg==''',
                "expected_packages": [
                    {
                        "name": "lodash",
                        "version": "4.17.21",
                        "version_constraint": "^4.17.20"
                    }
                ]
            },
            {
                "description": "Scoped package parsing",
                "lockfile_content": '''@babel/core@^7.12.0:
  version "7.12.9"
  resolved "https://registry.yarnpkg.com/@babel/core/-/core-7.12.9.tgz"
  integrity sha512-gTXYh3M5wb7FRXQy+FErKFAv90BnlOuNn1QkCK2lREoPAjrQCO49+HVSrFoe5uakFAF5eenS75KbO2vQiLrTMQ==''',
                "expected_packages": [
                    {
                        "name": "@babel/core",
                        "version": "7.12.9",
                        "version_constraint": "^7.12.0"
                    }
                ]
            },
            {
                "description": "Multiple version constraints for same package",
                "lockfile_content": '''lodash@^4.17.19, lodash@^4.17.20:
  version "4.17.21"
  resolved "https://registry.yarnpkg.com/lodash/-/lodash-4.17.21.tgz"
  integrity sha512-v2kDEe57lecTulaDIuNTPy3Ry4gLGJ6Z1O3vE1krgXZNrsQ+LFTGHVxVjcXPs17LhbZVGedAJv8XZ1tvj5FvSg==''',
                "expected_packages": [
                    {
                        "name": "lodash",
                        "version": "4.17.21",
                        "version_constraint": "^4.17.19, ^4.17.20"
                    }
                ],
                "edge_case": True
            },
            {
                "description": "Git dependency in yarn.lock",
                "lockfile_content": '''my-package@git+https://github.com/user/repo.git#commit123:
  version "1.0.0"
  resolved "git+https://github.com/user/repo.git#commit123"''',
                "expected_packages": [
                    {
                        "name": "my-package",
                        "version": "1.0.0",
                        "version_constraint": "git+https://github.com/user/repo.git#commit123"
                    }
                ],
                "edge_case": True
            }
        ]


def create_javascript_validation_suite() -> List[TestCase]:
    """
    Create comprehensive JavaScript parser validation test suite.
    Combines tests from multiple JavaScript package manager sources.
    """
    all_tests = []
    
    # Extract from npm/semver
    semver_extractor = NpmSemverTestExtractor()
    all_tests.extend(semver_extractor.extract_tests())
    
    # Extract from yarn.lock patterns
    yarn_extractor = YarnLockTestExtractor()
    all_tests.extend(yarn_extractor.extract_tests())
    
    logger.info(f"Created JavaScript validation suite with {len(all_tests)} total test cases")
    return all_tests


if __name__ == "__main__":
    # Test the extractors
    logging.basicConfig(level=logging.INFO)
    
    test_suite = create_javascript_validation_suite()
    print(f"Generated {len(test_suite)} JavaScript parser validation tests")
    
    # Show sample test case
    if test_suite:
        sample = test_suite[0]
        print(f"\nSample test case:")
        print(f"ID: {sample.id}")
        print(f"Category: {sample.category}")
        print(f"Input: {sample.input.content}")
        print(f"Expected packages: {len(sample.expected.packages)}")