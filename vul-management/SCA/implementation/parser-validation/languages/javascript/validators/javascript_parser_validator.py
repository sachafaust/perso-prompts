"""
JavaScript parser validator for testing against npm/yarn/pnpm test suites.
Validates JavaScript dependency parsing accuracy and edge case handling.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add the src directory to Python path for imports
base_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(base_path / "src"))

from parser_validation.common.validator_base import BaseParserValidator
from parser_validation.common.test_format import StandardizedTestCase, ValidationResult, CompatibilityReport
from sca_ai_scanner.parsers.javascript import JavaScriptParser

logger = logging.getLogger(__name__)


@dataclass
class JavaScriptValidationResult:
    """Result of JavaScript parser validation."""
    test_id: str
    passed: bool
    expected_packages: List[Dict[str, Any]]
    actual_packages: List[Dict[str, Any]]
    error_message: Optional[str] = None
    notes: Optional[str] = None


class JavaScriptParserValidator(ParserValidator):
    """
    Validator for JavaScript dependency parser using community test suites.
    Tests against npm/semver, yarn.lock, and pnpm parsing patterns.
    """
    
    def __init__(self, base_path: str):
        super().__init__(base_path)
        self.parser = JavaScriptParser(base_path)
        self.language = "javascript"
    
    def validate_test_case(self, test_case: TestCase) -> ValidationResult:
        """
        Validate a single JavaScript parser test case.
        Creates temporary files and tests parsing accuracy.
        """
        try:
            # Create temporary test file
            temp_file = self._create_temp_test_file(test_case)
            
            # Parse with our JavaScript parser
            actual_packages = self.parser.parse_file(temp_file)
            
            # Convert to validation format
            actual_package_data = [
                {
                    "name": pkg.name,
                    "version": pkg.version,
                    "ecosystem": pkg.ecosystem,
                    "source_locations": [
                        {
                            "file_path": loc.file_path,
                            "line_number": loc.line_number,
                            "declaration": loc.declaration,
                            "file_type": loc.file_type.value
                        } for loc in pkg.source_locations
                    ]
                } for pkg in actual_packages
            ]
            
            # Compare against expected results
            validation_result = self._compare_results(
                test_case.expected.packages,
                actual_package_data,
                test_case
            )
            
            # Clean up temp file
            temp_file.unlink()
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating test case {test_case.id}: {e}")
            return ValidationResult(
                test_id=test_case.id,
                passed=False,
                expected=test_case.expected.packages,
                actual=[],
                error=str(e),
                category=test_case.category
            )
    
    def _create_temp_test_file(self, test_case: TestCase) -> Path:
        """Create temporary test file based on test case input."""
        temp_dir = Path(self.base_path) / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        file_type = test_case.input.file_type
        if file_type == "package.json":
            filename = f"test_{test_case.id}_package.json"
            # Create valid package.json structure
            package_data = {
                "name": "test-package",
                "version": "1.0.0",
                "dependencies": {}
            }
            
            # Parse the test content to extract dependency
            content = test_case.input.content
            if ':' in content:
                # Handle format like '"lodash": "^4.17.20"'
                name_part, version_part = content.split(':', 1)
                name = name_part.strip().strip('"')
                version = version_part.strip().strip('"')
                package_data["dependencies"][name] = version
            
            temp_file = temp_dir / filename
            with open(temp_file, 'w') as f:
                json.dump(package_data, f, indent=2)
                
        elif file_type == "yarn.lock":
            filename = f"test_{test_case.id}_yarn.lock"
            temp_file = temp_dir / filename
            with open(temp_file, 'w') as f:
                f.write(test_case.input.content)
                
        else:
            # Generic file handling
            filename = f"test_{test_case.id}_{file_type}"
            temp_file = temp_dir / filename
            with open(temp_file, 'w') as f:
                f.write(test_case.input.content)
        
        return temp_file
    
    def _compare_results(
        self, 
        expected: List[Dict[str, Any]], 
        actual: List[Dict[str, Any]], 
        test_case: TestCase
    ) -> ValidationResult:
        """Compare expected vs actual parsing results."""
        
        # Create lookup dictionaries for comparison
        expected_lookup = {pkg["name"]: pkg for pkg in expected if pkg.get("name")}
        actual_lookup = {pkg["name"]: pkg for pkg in actual if pkg.get("name")}
        
        passed = True
        errors = []
        
        # Check each expected package
        for pkg_name, expected_pkg in expected_lookup.items():
            if pkg_name not in actual_lookup:
                passed = False
                errors.append(f"Missing expected package: {pkg_name}")
                continue
            
            actual_pkg = actual_lookup[pkg_name]
            
            # Compare versions (handle special cases)
            expected_version = expected_pkg.get("version")
            actual_version = actual_pkg.get("version")
            
            if expected_version is not None:
                # Handle JavaScript-specific version validation
                if not self._versions_match(expected_version, actual_version, test_case):
                    passed = False
                    errors.append(
                        f"Version mismatch for {pkg_name}: "
                        f"expected '{expected_version}', got '{actual_version}'"
                    )
            
            # Check version constraints if specified
            expected_constraint = expected_pkg.get("version_constraint")
            if expected_constraint and test_case.category == "version_constraints":
                # For version constraint tests, check if our parser handles constraints correctly
                satisfies = expected_pkg.get("satisfies_constraint", True)
                if not satisfies and actual_version is not None:
                    passed = False
                    errors.append(
                        f"Package {pkg_name} should not satisfy constraint {expected_constraint} "
                        f"but parser returned version {actual_version}"
                    )
        
        # Check for unexpected packages (false positives)
        unexpected_packages = set(actual_lookup.keys()) - set(expected_lookup.keys())
        if unexpected_packages:
            # Only flag as error if test explicitly checks for no extra packages
            if test_case.metadata and test_case.metadata.notes and "exact_match" in test_case.metadata.notes:
                passed = False
                errors.append(f"Unexpected packages found: {', '.join(unexpected_packages)}")
        
        return ValidationResult(
            test_id=test_case.id,
            passed=passed,
            expected=expected,
            actual=actual,
            error="; ".join(errors) if errors else None,
            category=test_case.category
        )
    
    def _versions_match(self, expected: str, actual: str, test_case: TestCase) -> bool:
        """
        Check if versions match, handling JavaScript-specific version formats.
        """
        if expected == actual:
            return True
        
        # Handle special JavaScript version cases
        if test_case.category == "version_constraints":
            # For constraint tests, we might expect normalized vs raw versions
            if expected.startswith(("^", "~", ">=", "<=", ">", "<")):
                # Our parser might normalize "^1.0.0" to "1.0.0"
                normalized_expected = self._normalize_version_for_comparison(expected)
                return normalized_expected == actual
        
        # Handle git/url dependencies
        if expected in ["git", "local", "latest", "next"]:
            return expected == actual
        
        # Handle npm tag matching
        if expected in ["latest", "next", "beta", "alpha"]:
            return expected == actual
        
        return False
    
    def _normalize_version_for_comparison(self, version: str) -> str:
        """Normalize version for comparison (similar to our parser's normalization)."""
        # Remove common npm version prefixes for comparison
        prefixes = ["^", "~", ">=", "<=", ">", "<", "="]
        for prefix in prefixes:
            if version.startswith(prefix):
                return version[len(prefix):].strip()
        return version
    
    def run_validation_suite(self, test_cases: List[TestCase]) -> ValidationSummary:
        """Run complete validation suite and generate summary."""
        results = []
        
        logger.info(f"Running JavaScript parser validation with {len(test_cases)} test cases")
        
        for test_case in test_cases:
            result = self.validate_test_case(test_case)
            results.append(result)
            
            if result.passed:
                logger.debug(f"✅ PASS: {test_case.id}")
            else:
                logger.warning(f"❌ FAIL: {test_case.id} - {result.error}")
        
        # Generate summary
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = total_tests - passed_tests
        
        # Category breakdown
        category_stats = {}
        for result in results:
            category = result.category
            if category not in category_stats:
                category_stats[category] = {"passed": 0, "total": 0}
            category_stats[category]["total"] += 1
            if result.passed:
                category_stats[category]["passed"] += 1
        
        compatibility_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        summary = ValidationSummary(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            compatibility_score=compatibility_score,
            category_breakdown=category_stats,
            failed_test_ids=[r.test_id for r in results if not r.passed]
        )
        
        logger.info(f"JavaScript parser validation complete: {compatibility_score:.1f}% compatibility")
        
        return summary, results


def run_javascript_validation() -> Dict[str, Any]:
    """
    Run JavaScript parser validation using extracted test cases.
    """
    from ..sources.npm_semver import create_javascript_validation_suite
    
    # Get base path for parser
    base_path = str(Path(__file__).parent.parent.parent.parent)
    
    # Create validator
    validator = JavaScriptParserValidator(base_path)
    
    # Get test cases
    test_cases = create_javascript_validation_suite()
    
    # Run validation
    summary, detailed_results = validator.run_validation_suite(test_cases)
    
    # Generate report
    report = {
        "parser": "JavaScriptParser",
        "language": "javascript",
        "validation_date": "2025-01-24",
        "summary": {
            "total_tests": summary.total_tests,
            "passed_tests": summary.passed_tests,  
            "failed_tests": summary.failed_tests,
            "compatibility_score": summary.compatibility_score
        },
        "category_breakdown": summary.category_breakdown,
        "failed_tests": [
            {
                "test_id": result.test_id,
                "category": result.category,
                "error": result.error,
                "expected": result.expected,
                "actual": result.actual
            }
            for result in detailed_results if not result.passed
        ],
        "recommendations": _generate_recommendations(summary, detailed_results)
    }
    
    return report


def _generate_recommendations(summary: ValidationSummary, results: List[ValidationResult]) -> List[str]:
    """Generate improvement recommendations based on validation results."""
    recommendations = []
    
    if summary.compatibility_score < 90:
        recommendations.append("Improve overall parser compatibility to reach 90%+ target")
    
    # Analyze failure patterns
    error_patterns = {}
    for result in results:
        if not result.passed and result.error:
            # Extract error type
            if "Missing expected package" in result.error:
                error_patterns["missing_packages"] = error_patterns.get("missing_packages", 0) + 1
            elif "Version mismatch" in result.error:
                error_patterns["version_mismatch"] = error_patterns.get("version_mismatch", 0) + 1
            elif "constraint" in result.error:
                error_patterns["constraint_handling"] = error_patterns.get("constraint_handling", 0) + 1
    
    # Add specific recommendations
    if error_patterns.get("version_mismatch", 0) > 3:
        recommendations.append("Improve JavaScript version constraint parsing (^, ~, >=, etc.)")
    
    if error_patterns.get("missing_packages", 0) > 2:
        recommendations.append("Fix package name extraction for complex dependency formats")
    
    if error_patterns.get("constraint_handling", 0) > 1:
        recommendations.append("Implement proper semver constraint validation")
    
    # Category-specific recommendations
    for category, stats in summary.category_breakdown.items():
        success_rate = (stats["passed"] / stats["total"]) * 100
        if success_rate < 80:
            if category == "version_constraints":
                recommendations.append("Implement comprehensive npm semver constraint handling")
            elif category == "lockfile_parsing":
                recommendations.append("Improve yarn.lock and package-lock.json parsing accuracy")
    
    return recommendations


if __name__ == "__main__":
    # Run validation
    logging.basicConfig(level=logging.INFO)
    
    report = run_javascript_validation()
    
    print(f"JavaScript Parser Validation Report")
    print(f"=" * 40)
    print(f"Compatibility Score: {report['summary']['compatibility_score']:.1f}%")
    print(f"Tests Passed: {report['summary']['passed_tests']}/{report['summary']['total_tests']}")
    print(f"\nCategory Breakdown:")
    for category, stats in report['category_breakdown'].items():
        success_rate = (stats['passed'] / stats['total']) * 100
        print(f"  {category}: {success_rate:.1f}% ({stats['passed']}/{stats['total']})")
    
    if report['failed_tests']:
        print(f"\nFailed Tests ({len(report['failed_tests'])}):")
        for failure in report['failed_tests'][:5]:  # Show first 5 failures
            print(f"  {failure['test_id']}: {failure['error']}")
        if len(report['failed_tests']) > 5:
            print(f"  ... and {len(report['failed_tests']) - 5} more")
    
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")