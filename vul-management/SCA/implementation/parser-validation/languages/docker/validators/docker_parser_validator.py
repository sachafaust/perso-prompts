"""
Docker parser validator - comprehensive testing for Docker dependency parsing.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Set

from ....common.validator_base import ValidatorBase
from ....common.test_format import TestCase, ValidationResult
from .....src.sca_ai_scanner.parsers.docker import DockerParser
from .....src.sca_ai_scanner.core.models import Package

logger = logging.getLogger(__name__)


class DockerParserValidator(ValidatorBase):
    """Validator for Docker parser implementation."""
    
    def __init__(self):
        super().__init__()
        self.parser = DockerParser("/tmp/test-project")
        
    def get_test_data_dir(self) -> Path:
        """Get the test data directory for Docker tests."""
        return Path(__file__).parent.parent / "test-data"
    
    def validate_parser(self, test_case: TestCase) -> ValidationResult:
        """Validate Docker parser against a test case."""
        try:
            # Create temporary Dockerfile
            temp_file = self.create_temp_file(test_case.input, suffix=".Dockerfile")
            
            # Parse the file
            packages = self.parser.parse_file(temp_file)
            
            # Convert to comparable format
            found_packages = self._packages_to_dict(packages)
            expected_packages = self._normalize_expected(test_case.expected_packages)
            
            # Compare results
            missing = self._find_missing_packages(expected_packages, found_packages)
            extra = self._find_extra_packages(expected_packages, found_packages)
            
            success = len(missing) == 0 and len(extra) == 0
            
            return ValidationResult(
                test_name=test_case.name,
                success=success,
                expected=expected_packages,
                actual=found_packages,
                missing_packages=missing,
                extra_packages=extra,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Error validating test case {test_case.name}: {e}")
            return ValidationResult(
                test_name=test_case.name,
                success=False,
                expected=test_case.expected_packages,
                actual=[],
                missing_packages=[],
                extra_packages=[],
                error_message=str(e)
            )
        finally:
            # Cleanup
            if 'temp_file' in locals():
                temp_file.unlink(missing_ok=True)
    
    def _packages_to_dict(self, packages: List[Package]) -> List[Dict[str, Any]]:
        """Convert Package objects to comparable dictionaries."""
        return [
            {
                "name": pkg.name,
                "version": pkg.version,
                "ecosystem": pkg.ecosystem
            }
            for pkg in packages
        ]
    
    def _normalize_expected(self, expected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize expected packages for comparison."""
        normalized = []
        for pkg in expected:
            normalized_pkg = {
                "name": pkg["name"],
                "version": pkg.get("version", "latest"),
                "ecosystem": pkg.get("ecosystem", "docker")
            }
            normalized.append(normalized_pkg)
        return normalized
    
    def _find_missing_packages(
        self, 
        expected: List[Dict[str, Any]], 
        found: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find packages that were expected but not found."""
        missing = []
        for exp_pkg in expected:
            if not self._package_in_list(exp_pkg, found):
                missing.append(exp_pkg)
        return missing
    
    def _find_extra_packages(
        self, 
        expected: List[Dict[str, Any]], 
        found: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find packages that were found but not expected."""
        extra = []
        for found_pkg in found:
            if not self._package_in_list(found_pkg, expected):
                extra.append(found_pkg)
        return extra
    
    def _package_in_list(
        self, 
        package: Dict[str, Any], 
        package_list: List[Dict[str, Any]]
    ) -> bool:
        """Check if a package exists in the list."""
        for pkg in package_list:
            if (pkg["name"] == package["name"] and 
                pkg["ecosystem"] == package["ecosystem"]):
                # For version comparison, handle special cases
                if package["version"] == "latest" or pkg["version"] == "latest":
                    return True
                # Handle version prefixes (>=, <=, etc.)
                if self._versions_match(pkg["version"], package["version"]):
                    return True
        return False
    
    def _versions_match(self, version1: str, version2: str) -> bool:
        """Check if two versions match, handling constraints."""
        # Direct match
        if version1 == version2:
            return True
        
        # Handle version constraints for pip/npm packages
        # This is simplified - real implementation would parse constraints
        v1_base = version1.split(',')[0].lstrip('>=<~!')
        v2_base = version2.split(',')[0].lstrip('>=<~!')
        
        return v1_base == v2_base
    
    def run_validation_suite(self) -> Dict[str, Any]:
        """Run complete Docker parser validation suite."""
        results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "test_categories": {}
        }
        
        # Test categories
        test_categories = [
            "dockerfile/base_images.yaml",
            "dockerfile/system_packages.yaml",
            "dockerfile/language_packages.yaml",
            "dockerfile/complex_scenarios.yaml",
            "docker-compose/basic.yaml"
        ]
        
        for category in test_categories:
            category_path = self.get_test_data_dir() / category
            if category_path.exists():
                category_results = self.run_test_file(category_path)
                results["test_categories"][category] = category_results
                results["total_tests"] += category_results["total"]
                results["passed"] += category_results["passed"]
                results["failed"] += category_results["failed"]
        
        return results


def main():
    """Run Docker parser validation."""
    logging.basicConfig(level=logging.INFO)
    
    validator = DockerParserValidator()
    results = validator.run_validation_suite()
    
    print("\n" + "="*60)
    print("Docker Parser Validation Results")
    print("="*60)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {(results['passed']/results['total_tests']*100):.1f}%")
    
    print("\nCategory Breakdown:")
    for category, cat_results in results["test_categories"].items():
        print(f"\n{category}:")
        print(f"  Total: {cat_results['total']}")
        print(f"  Passed: {cat_results['passed']}")
        print(f"  Failed: {cat_results['failed']}")
        
        if cat_results["failed_tests"]:
            print("  Failed Tests:")
            for failed in cat_results["failed_tests"]:
                print(f"    - {failed['test_name']}: {failed.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()