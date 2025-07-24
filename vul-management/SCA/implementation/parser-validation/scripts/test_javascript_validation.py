"""
JavaScript parser validation test script.
Quick validation to test JavaScript parser against known edge cases.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
base_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(base_dir / "src"))

from sca_ai_scanner.parsers.javascript import JavaScriptParser

logger = logging.getLogger(__name__)


def create_test_files(test_dir: Path) -> Dict[str, Path]:
    """Create JavaScript test files for validation."""
    test_dir.mkdir(exist_ok=True)
    
    test_files = {}
    
    # Test 1: Basic package.json with version constraints
    package_json_content = {
        "name": "test-project",
        "version": "1.0.0",
        "dependencies": {
            "lodash": "^4.17.20",
            "express": "~4.18.0",
            "react": ">=17.0.0",
            "@babel/core": "^7.12.0",
            "exact-version": "1.0.0"
        },
        "devDependencies": {
            "jest": "^27.0.0",
            "webpack": "^5.0.0"
        }
    }
    
    package_json_file = test_dir / "package.json"
    with open(package_json_file, 'w') as f:
        json.dump(package_json_content, f, indent=2)
    test_files["package.json"] = package_json_file
    
    # Test 2: yarn.lock with complex dependencies  
    yarn_lock_content = '''# yarn lockfile v1

lodash@^4.17.20:
  version "4.17.21"
  resolved "https://registry.yarnpkg.com/lodash/-/lodash-4.17.21.tgz"
  integrity sha512-v2kDEe57lecTulaDIuNTPy3Ry4gLGJ6Z1O3vE1krgXZNrsQ+LFTGHVxVjcXPs17LhbZVGedAJv8XZ1tvj5FvSg==

"@babel/core@^7.12.0":
  version "7.12.9"
  resolved "https://registry.yarnpkg.com/@babel/core/-/core-7.12.9.tgz"
  integrity sha512-gTXYh3M5wb7FRXQy+FErKFAv90BnlOuNn1QkCK2lREoPAjrQCO49+HVSrFoe5uakFAF5eenS75KbO2vQiLrTMQ==

react@^17.0.0, react@^17.0.1:
  version "17.0.2"  
  resolved "https://registry.yarnpkg.com/react/-/react-17.0.2.tgz"
  integrity sha512-gnhPt75i/dq/z3/6q/0asP78D0u592D5L1pd7M8P+dck6Fu/jJeL6iVVK23fptSUZj8Vjf++7wXA8UNclGQcbA==

express@~4.18.0:
  version "4.18.2"
  resolved "https://registry.yarnpkg.com/express/-/express-4.18.2.tgz"
'''
    
    yarn_lock_file = test_dir / "yarn.lock"
    with open(yarn_lock_file, 'w') as f:
        f.write(yarn_lock_content)
    test_files["yarn.lock"] = yarn_lock_file
    
    # Test 3: package-lock.json (npm v2 format)
    package_lock_content = {
        "name": "test-project",
        "version": "1.0.0", 
        "lockfileVersion": 2,
        "requires": True,
        "packages": {
            "": {
                "name": "test-project",
                "version": "1.0.0"
            },
            "node_modules/lodash": {
                "version": "4.17.21",
                "resolved": "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz"
            },
            "node_modules/@babel/core": {
                "version": "7.12.9",
                "resolved": "https://registry.npmjs.org/@babel/core/-/core-7.12.9.tgz"
            },
            "node_modules/jest": {
                "version": "27.5.1",
                "dev": True
            }
        },
        "dependencies": {
            "lodash": {
                "version": "4.17.21",
                "resolved": "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz"
            },
            "@babel/core": {
                "version": "7.12.9", 
                "resolved": "https://registry.npmjs.org/@babel/core/-/core-7.12.9.tgz"
            }
        }
    }
    
    package_lock_file = test_dir / "package-lock.json"
    with open(package_lock_file, 'w') as f:
        json.dump(package_lock_content, f, indent=2)
    test_files["package-lock.json"] = package_lock_file
    
    return test_files


def validate_javascript_parser() -> Dict[str, Any]:
    """Run JavaScript parser validation tests."""
    
    # Setup
    test_dir = Path("/tmp/js_parser_test")
    parser = JavaScriptParser(str(test_dir))
    
    # Create test files
    test_files = create_test_files(test_dir)
    
    results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_results": [],
        "compatibility_score": 0
    }
    
    expected_results = {
        "package.json": {
            "expected_packages": {
                "lodash", "express", "react", "@babel/core", "exact-version"
            },
            "expected_versions": {
                "lodash": ("4.17.20", "caret"),  # Normalized from ^4.17.20
                "express": ("4.18.0", "tilde"),  # Normalized from ~4.18.0
                "react": ("17.0.0", "gte"),     # Normalized from >=17.0.0
                "@babel/core": ("7.12.0", "caret"),
                "exact-version": ("1.0.0", "exact")
            },
            "excluded_packages": {"jest", "webpack"}  # devDependencies should be excluded
        },
        "yarn.lock": {
            "expected_packages": {
                "lodash", "@babel/core", "react", "express"
            },
            "expected_versions": {
                "lodash": "4.17.21",
                "@babel/core": "7.12.9", 
                "react": "17.0.2",
                "express": "4.18.2"
            }
        },
        "package-lock.json": {
            "expected_packages": {
                "lodash", "@babel/core"  # jest should be excluded as dev dependency
            },
            "expected_versions": {
                "lodash": "4.17.21",
                "@babel/core": "7.12.9"
            },
            "excluded_packages": {"jest"}
        }
    }
    
    # Run tests for each file type
    for file_type, file_path in test_files.items():
        try:
            print(f"\n🧪 Testing {file_type}...")
            
            # Parse the file
            packages = parser.parse_file(file_path)
            
            # Convert to set for comparison
            actual_packages = {pkg.name for pkg in packages}
            actual_versions = {pkg.name: pkg.version for pkg in packages}
            
            # Get expected results for this file type
            expected = expected_results[file_type]
            expected_packages = expected["expected_packages"]
            
            # Test 1: Check package names
            missing_packages = expected_packages - actual_packages
            unexpected_packages = actual_packages - expected_packages
            
            # Test 2: Check excluded packages (if any)
            excluded_packages = expected.get("excluded_packages", set())
            incorrectly_included = actual_packages & excluded_packages
            
            # Test 3: Check versions (where applicable)
            version_mismatches = []
            if "expected_versions" in expected:
                for pkg_name, expected_version in expected["expected_versions"].items():
                    if pkg_name in actual_versions:
                        actual_version = actual_versions[pkg_name]
                        if isinstance(expected_version, tuple):
                            expected_ver, constraint_type = expected_version
                            # For package.json, we expect normalized versions
                            if actual_version != expected_ver:
                                version_mismatches.append(
                                    f"{pkg_name}: expected {expected_ver}, got {actual_version}"
                                )
                        else:
                            # Exact version match expected
                            if actual_version != expected_version:
                                version_mismatches.append(
                                    f"{pkg_name}: expected {expected_version}, got {actual_version}"
                                )
            
            # Determine if test passed
            test_passed = (
                len(missing_packages) == 0 and
                len(incorrectly_included) == 0 and
                len(version_mismatches) == 0
            )
            
            # Record results
            test_result = {
                "file_type": file_type,
                "passed": test_passed,
                "total_packages": len(packages),
                "expected_count": len(expected_packages),
                "missing_packages": list(missing_packages),
                "unexpected_packages": list(unexpected_packages),
                "incorrectly_included": list(incorrectly_included),
                "version_mismatches": version_mismatches,
                "actual_packages": [
                    {"name": pkg.name, "version": pkg.version, "ecosystem": pkg.ecosystem}
                    for pkg in packages
                ]
            }
            
            results["test_results"].append(test_result)
            results["total_tests"] += 1
            
            if test_passed:
                results["passed_tests"] += 1
                print(f"✅ PASS: {file_type}")
            else:
                results["failed_tests"] += 1
                print(f"❌ FAIL: {file_type}")
                if missing_packages:
                    print(f"   Missing packages: {missing_packages}")
                if incorrectly_included:
                    print(f"   Should not include: {incorrectly_included}")
                if version_mismatches:
                    print(f"   Version mismatches: {version_mismatches}")
            
            # Show details
            print(f"   Found {len(packages)} packages: {sorted(actual_packages)}")
            
        except Exception as e:
            print(f"❌ ERROR: {file_type} - {e}")
            results["test_results"].append({
                "file_type": file_type,
                "passed": False,
                "error": str(e)
            })
            results["total_tests"] += 1
            results["failed_tests"] += 1
    
    # Calculate compatibility score
    if results["total_tests"] > 0:
        results["compatibility_score"] = (results["passed_tests"] / results["total_tests"]) * 100
    
    # Cleanup
    for file_path in test_files.values():
        file_path.unlink(missing_ok=True)
    test_dir.rmdir()
    
    return results


def analyze_javascript_parser_issues(results: Dict[str, Any]) -> List[str]:
    """Analyze test results and generate improvement recommendations."""
    recommendations = []
    
    if results["compatibility_score"] < 90:
        recommendations.append(f"Overall compatibility is {results['compatibility_score']:.1f}% - target 90%+")
    
    # Analyze specific failure patterns
    missing_package_count = 0
    version_mismatch_count = 0
    dev_exclusion_issues = 0
    
    for test_result in results["test_results"]:
        if not test_result["passed"]:
            missing_package_count += len(test_result.get("missing_packages", []))
            version_mismatch_count += len(test_result.get("version_mismatches", []))
            dev_exclusion_issues += len(test_result.get("incorrectly_included", []))
    
    if missing_package_count > 0:
        recommendations.append(f"Fix package name extraction ({missing_package_count} missing packages)")
    
    if version_mismatch_count > 0:
        recommendations.append(f"Improve version parsing/normalization ({version_mismatch_count} mismatches)")
    
    if dev_exclusion_issues > 0:
        recommendations.append(f"Fix dev dependency exclusion logic ({dev_exclusion_issues} issues)")
    
    # File-type specific recommendations
    for test_result in results["test_results"]:
        if not test_result["passed"]:
            file_type = test_result["file_type"]
            if file_type == "yarn.lock":
                recommendations.append("Improve yarn.lock parsing - check package name extraction logic")
            elif file_type == "package-lock.json":
                recommendations.append("Fix package-lock.json parsing - verify dev dependency filtering")
            elif file_type == "package.json":
                recommendations.append("Enhance package.json version constraint normalization")
    
    return recommendations


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 JavaScript Parser Validation")
    print("=" * 40)
    
    # Run validation tests
    results = validate_javascript_parser()
    
    # Print summary
    print(f"\n📊 Results Summary:")
    print(f"   Total tests: {results['total_tests']}")
    print(f"   Passed: {results['passed_tests']}")
    print(f"   Failed: {results['failed_tests']}")
    print(f"   Compatibility Score: {results['compatibility_score']:.1f}%")
    
    # Generate recommendations
    recommendations = analyze_javascript_parser_issues(results)
    if recommendations:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    # Detailed results
    print(f"\n📋 Detailed Results:")
    for test_result in results["test_results"]:
        if test_result["passed"]:
            print(f"✅ {test_result['file_type']}: {test_result['total_packages']} packages parsed")
        else:
            print(f"❌ {test_result['file_type']}: {test_result.get('error', 'Multiple issues')}")
    
    print(f"\n🎯 JavaScript parser validation {'PASSED' if results['compatibility_score'] >= 90 else 'NEEDS IMPROVEMENT'}")