"""
Base classes for parser validation across languages.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from .test_format import StandardizedTestCase, ValidationResult, CompatibilityReport


class BaseParserValidator(ABC):
    """Base class for validating parsers against test suites."""
    
    def __init__(self, parser_name: str):
        """
        Initialize the validator.
        
        Args:
            parser_name: Name of the parser being validated
        """
        self.parser_name = parser_name
        self.results: List[ValidationResult] = []
    
    @abstractmethod
    def parse_dependency_file(self, content: str, file_type: str) -> Dict[str, Any]:
        """
        Parse dependency file content using the target parser.
        
        Args:
            content: File content to parse
            file_type: Type of dependency file
            
        Returns:
            Parsed dependency information
        """
        pass
    
    def run_validation(self, test_cases: List[StandardizedTestCase]) -> List[ValidationResult]:
        """
        Run validation against a list of test cases.
        
        Args:
            test_cases: Test cases to validate against
            
        Returns:
            List of validation results
        """
        self.results = []
        
        for test_case in test_cases:
            print(f"Running test: {test_case.id}")
            result = self.validate_single_test(test_case)
            self.results.append(result)
        
        return self.results
    
    def validate_single_test(self, test_case: StandardizedTestCase) -> ValidationResult:
        """
        Validate parser against a single test case.
        
        Args:
            test_case: Test case to validate
            
        Returns:
            Validation result
        """
        try:
            # Parse using our parser
            actual_result = self.parse_dependency_file(
                test_case.input.content,
                test_case.input.file_type.value
            )
            
            # Compare with expected result
            passed, differences = self.compare_results(actual_result, test_case.expected)
            
            return ValidationResult(
                test_id=test_case.id,
                passed=passed,
                actual_result=actual_result,
                expected_result=self._expected_to_dict(test_case.expected),
                differences=differences
            )
            
        except Exception as e:
            return ValidationResult(
                test_id=test_case.id,
                passed=False,
                actual_result={},
                expected_result=self._expected_to_dict(test_case.expected),
                differences=[],
                error=str(e)
            )
    
    def compare_results(self, actual: Dict[str, Any], expected) -> tuple[bool, List[str]]:
        """
        Compare actual parser results with expected results.
        
        Args:
            actual: Actual parser output
            expected: Expected test results
            
        Returns:
            Tuple of (passed, list of differences)
        """
        differences = []
        
        # If test expects an error
        if expected.error:
            if 'error' not in actual:
                differences.append("Expected parsing error but parsing succeeded")
            return len(differences) == 0, differences
        
        # Compare packages
        actual_packages = actual.get('packages', [])
        expected_packages = expected.packages
        
        if len(actual_packages) != len(expected_packages):
            differences.append(
                f"Package count mismatch: expected {len(expected_packages)}, got {len(actual_packages)}"
            )
        
        # Compare each package
        for i, expected_pkg in enumerate(expected_packages):
            if i >= len(actual_packages):
                differences.append(f"Missing package at index {i}: {expected_pkg.name}")
                continue
                
            actual_pkg = actual_packages[i]
            pkg_diffs = self.compare_packages(actual_pkg, expected_pkg)
            differences.extend([f"Package {i} ({expected_pkg.name}): {diff}" for diff in pkg_diffs])
        
        return len(differences) == 0, differences
    
    def compare_packages(self, actual_pkg: Dict[str, Any], expected_pkg) -> List[str]:
        """
        Compare individual package results.
        
        Args:
            actual_pkg: Actual package data
            expected_pkg: Expected package data
            
        Returns:
            List of differences
        """
        differences = []
        
        # Check required fields
        if actual_pkg.get('name') != expected_pkg.name:
            differences.append(f"Name mismatch: expected '{expected_pkg.name}', got '{actual_pkg.get('name')}'")
        
        if actual_pkg.get('version_constraint') != expected_pkg.version_constraint:
            differences.append(
                f"Version constraint mismatch: expected '{expected_pkg.version_constraint}', "
                f"got '{actual_pkg.get('version_constraint')}'"
            )
        
        if actual_pkg.get('environment_marker') != expected_pkg.environment_marker:
            differences.append(
                f"Environment marker mismatch: expected '{expected_pkg.environment_marker}', "
                f"got '{actual_pkg.get('environment_marker')}'"
            )
        
        # Check extras
        actual_extras = set(actual_pkg.get('extras', []))
        expected_extras = set(expected_pkg.extras)
        if actual_extras != expected_extras:
            differences.append(f"Extras mismatch: expected {expected_extras}, got {actual_extras}")
        
        return differences
    
    def generate_compatibility_report(self, source_project: str) -> CompatibilityReport:
        """
        Generate comprehensive compatibility report.
        
        Args:
            source_project: Name of source project tests came from
            
        Returns:
            Compatibility report
        """
        if not self.results:
            raise ValueError("No validation results available. Run validation first.")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        compatibility_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Group by category (if available in test IDs)
        categories = {}
        for result in self.results:
            # Extract category from test ID (e.g., "pip-tools-env-marker-001" -> "env-marker")
            parts = result.test_id.split('-')
            if len(parts) >= 3:
                category = '-'.join(parts[1:-1])  # Skip project name and number
            else:
                category = "uncategorized"
            
            if category not in categories:
                categories[category] = {"passed": 0, "total": 0}
            
            categories[category]["total"] += 1
            if result.passed:
                categories[category]["passed"] += 1
        
        # Collect failures
        failures = []
        for result in self.results:
            if not result.passed:
                failure_info = {
                    "test_id": result.test_id,
                    "differences": result.differences,
                    "error": result.error
                }
                failures.append(failure_info)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(categories, failures)
        
        return CompatibilityReport(
            report_version="1.0",
            test_date=datetime.now().isoformat(),
            parser=self.parser_name,
            source_project=source_project,
            summary={
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "compatibility_score": round(compatibility_score, 2)
            },
            categories=categories,
            failures=failures,
            recommendations=recommendations
        )
    
    def _expected_to_dict(self, expected) -> Dict[str, Any]:
        """Convert expected results to dictionary format."""
        return {
            "packages": [
                {
                    "name": pkg.name,
                    "version_constraint": pkg.version_constraint,
                    "environment_marker": pkg.environment_marker,
                    "extras": pkg.extras,
                    "url": pkg.url,
                    "editable": pkg.editable,
                    "hash_values": pkg.hash_values
                } for pkg in expected.packages
            ],
            "error": expected.error
        }
    
    def _generate_recommendations(self, categories: Dict, failures: List[Dict]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Analyze common failure patterns
        common_issues = {}
        for failure in failures:
            for diff in failure.get("differences", []):
                # Extract issue type from difference message
                if "Name mismatch" in diff:
                    common_issues["name_parsing"] = common_issues.get("name_parsing", 0) + 1
                elif "Version constraint" in diff:
                    common_issues["version_parsing"] = common_issues.get("version_parsing", 0) + 1
                elif "Environment marker" in diff:
                    common_issues["environment_markers"] = common_issues.get("environment_markers", 0) + 1
                elif "Extras" in diff:
                    common_issues["extras_parsing"] = common_issues.get("extras_parsing", 0) + 1
        
        # Generate recommendations based on issues
        if common_issues.get("environment_markers", 0) > 0:
            recommendations.append("Improve environment marker parsing logic")
        
        if common_issues.get("version_parsing", 0) > 0:
            recommendations.append("Review version constraint parsing for edge cases")
        
        if common_issues.get("extras_parsing", 0) > 0:
            recommendations.append("Add support for complex extras syntax")
        
        # Category-specific recommendations
        for category, stats in categories.items():
            pass_rate = (stats["passed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            if pass_rate < 80:
                recommendations.append(f"Focus improvement efforts on {category} test cases")
        
        return recommendations