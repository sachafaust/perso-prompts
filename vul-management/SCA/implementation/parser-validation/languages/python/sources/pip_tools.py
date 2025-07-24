"""
Test extractor for pip-tools repository.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    # Try relative import first (when imported as module)
    from ....common.extractor_base import BaseTestExtractor, PYTHON_SOURCES
    from ....common.test_format import (
        StandardizedTestCase, TestInput, TestExpected, TestMetadata,
        ExpectedPackage, FileType, TestCategory, Difficulty
    )
except ImportError:
    # Fall back to absolute import (when run as script)
    from common.extractor_base import BaseTestExtractor, PYTHON_SOURCES
    from common.test_format import (
        StandardizedTestCase, TestInput, TestExpected, TestMetadata,
        ExpectedPackage, FileType, TestCategory, Difficulty
    )


class PipToolsTestExtractor(BaseTestExtractor):
    """Extract test cases from pip-tools repository."""
    
    def __init__(self, version: str = "7.4.1"):
        """
        Initialize pip-tools test extractor.
        
        Args:
            version: pip-tools version to extract from
        """
        source_info = PYTHON_SOURCES["pip-tools"]
        super().__init__(source_info.repo_url, version)
        self.source_info = source_info
    
    def extract_tests(self) -> List[StandardizedTestCase]:
        """Extract test cases from pip-tools repository."""
        if not self.repo_path:
            raise RuntimeError("Repository not cloned. Use context manager.")
        
        test_files = self.get_test_files()
        all_tests = []
        
        for test_file in test_files:
            print(f"Parsing {test_file.name}...")
            try:
                file_tests = self.parse_test_file(test_file)
                all_tests.extend(file_tests)
            except Exception as e:
                print(f"Error parsing {test_file}: {e}")
                continue
        
        # Filter to only relevant tests
        relevant_tests = self.filter_relevant_tests(all_tests)
        
        print(f"Extracted {len(relevant_tests)} relevant tests from {len(all_tests)} total tests")
        return relevant_tests
    
    def get_test_files(self) -> List[Path]:
        """Get pip-tools test files to analyze."""
        test_dir = self.repo_path / "tests"
        if not test_dir.exists():
            raise FileNotFoundError(f"Test directory not found: {test_dir}")
        
        # Focus on key test files for dependency parsing
        target_files = [
            "test_cli_compile.py",  # Requirements compilation edge cases
            "test_resolver.py",     # Dependency resolution logic
            "test_repository_pypi.py",  # PyPI integration
            "test_utils.py",        # Utility functions
        ]
        
        test_files = []
        for filename in target_files:
            file_path = test_dir / filename
            if file_path.exists():
                test_files.append(file_path)
            else:
                print(f"Warning: {filename} not found in {test_dir}")
        
        return test_files
    
    def parse_test_file(self, file_path: Path) -> List[StandardizedTestCase]:
        """Parse a single pip-tools test file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"Failed to parse {file_path}: {e}")
            return []
        
        tests = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                test_case = self.extract_test_case_from_function(node, file_path)
                if test_case:
                    tests.append(test_case)
        
        return tests
    
    def extract_test_case_from_function(self, func_node: ast.FunctionDef, 
                                      file_path: Path) -> Optional[StandardizedTestCase]:
        """Extract test case from a test function AST node."""
        # Get function source code
        try:
            # This is a simplified extraction - in practice, we'd need more sophisticated parsing
            func_source = ast.get_source_segment(open(file_path).read(), func_node)
            if not func_source:
                return None
        except:
            return None
        
        # Look for requirements-like strings in the function
        requirements_patterns = [
            r'["\']([^"\']+==[\d\.]+[^"\']*)["\']',  # Simple version pins
            r'["\']([^"\']+>=[\d\.]+[^"\']*)["\']',  # Minimum versions
            r'["\']([^"\']+~=[\d\.]+[^"\']*)["\']',  # Compatible versions
            r'["\']([^"\']+;[^"\']*)["\']',          # Environment markers
            r'["\'](-e [^"\']+)["\']',               # Editable installs
            r'["\']([^"\']+\[[\w,]+\][^"\']*)["\']', # Extras
        ]
        
        found_requirements = []
        for pattern in requirements_patterns:
            matches = re.findall(pattern, func_source, re.MULTILINE)
            found_requirements.extend(matches)
        
        if not found_requirements:
            return None
        
        # Take the first requirement for simplicity (in practice, we'd be more sophisticated)
        requirement = found_requirements[0]
        
        # Determine test category based on content
        category = self._determine_category(requirement, func_node.name)
        
        # Parse the requirement to create expected result
        expected_package = self._parse_requirement_string(requirement)
        if not expected_package:
            return None
        
        # Create standardized test case
        test_id = f"pip-tools-{category.value}-{abs(hash(func_node.name)) % 1000:03d}"
        source_ref = f"pip-tools/{file_path.name}::{func_node.name}"
        
        return StandardizedTestCase(
            id=test_id,
            source=source_ref,
            category=category,
            input=TestInput(
                content=requirement,
                file_type=FileType.REQUIREMENTS_TXT
            ),
            expected=TestExpected(
                packages=[expected_package]
            ),
            metadata=TestMetadata(
                difficulty=self._determine_difficulty(requirement),
                edge_case=self._is_edge_case(requirement, func_node.name),
                extraction_date=datetime.now().strftime("%Y-%m-%d"),
                source_version=f"pip-tools@{self.version}",
                notes=f"Extracted from {func_node.name}"
            )
        )
    
    def _determine_category(self, requirement: str, func_name: str) -> TestCategory:
        """Determine test category based on requirement content and function name."""
        func_name_lower = func_name.lower()
        req_lower = requirement.lower()
        
        if ';' in requirement:
            return TestCategory.ENVIRONMENT_MARKERS
        elif requirement.startswith('-e'):
            return TestCategory.EDITABLE_INSTALLS
        elif '[' in requirement and ']' in requirement:
            return TestCategory.EXTRAS
        elif any(op in requirement for op in ['>=', '<=', '!=', '~=', '==']):
            if ',' in requirement or '!=' in requirement:
                return TestCategory.COMPLEX_CONSTRAINTS
            else:
                return TestCategory.BASIC_PARSING
        elif 'git+' in requirement or 'http' in requirement:
            return TestCategory.URL_DEPENDENCIES
        elif 'environment' in func_name_lower or 'marker' in func_name_lower:
            return TestCategory.ENVIRONMENT_MARKERS
        elif 'constraint' in func_name_lower or 'version' in func_name_lower:
            return TestCategory.VERSION_CONSTRAINTS
        else:
            return TestCategory.BASIC_PARSING
    
    def _determine_difficulty(self, requirement: str) -> Difficulty:
        """Determine test difficulty based on requirement complexity."""
        complexity_score = 0
        
        # Count complexity indicators
        if ';' in requirement:
            complexity_score += 2  # Environment markers
        if requirement.count(',') > 0:
            complexity_score += 1  # Multiple constraints
        if any(op in requirement for op in ['!=', '~=']):
            complexity_score += 1  # Complex operators
        if '[' in requirement:
            complexity_score += 1  # Extras
        if requirement.startswith('-e'):
            complexity_score += 2  # Editable installs
        if any(url in requirement for url in ['git+', 'http', 'file:']):
            complexity_score += 2  # URL dependencies
        
        if complexity_score >= 4:
            return Difficulty.EXPERT
        elif complexity_score >= 2:
            return Difficulty.HARD
        elif complexity_score >= 1:
            return Difficulty.MEDIUM
        else:
            return Difficulty.EASY
    
    def _is_edge_case(self, requirement: str, func_name: str) -> bool:
        """Determine if this is an edge case test."""
        edge_indicators = [
            'edge', 'corner', 'complex', 'special', 'weird', 'unusual',
            'error', 'fail', 'invalid', 'malformed'
        ]
        
        func_name_lower = func_name.lower()
        return any(indicator in func_name_lower for indicator in edge_indicators)
    
    def _is_invalid_requirement(self, requirement: str) -> bool:
        """Check if requirement string is invalid and should be filtered out."""
        # Filter out common invalid patterns
        invalid_patterns = [
            # Template variables
            '{',
            '}',
            'tmp_path',
            'test_package',
            'url}',
            
            # Multi-line strings and code fragments
            '\n        ',
            '\n    ',
            '\\n',
            '\\\\',
            
            # Python code patterns
            'def ',
            'class ',
            'import ',
            'from ',
            'assert ',
            'kwargs[',
            'args,',
            'runner.invoke',
            'cli,',
            
            # Configuration file content
            '[global]',
            '[project]',
            'index-url',
            'invalid =',
            
            # Test artifacts
            'pass\n',
            'Test that',
            'torchvision',
            'patches (',
        ]
        
        # Check for invalid patterns
        for pattern in invalid_patterns:
            if pattern in requirement:
                return True
        
        # Must contain at least one valid package character
        if not re.search(r'[a-zA-Z0-9\-_]', requirement):
            return True
        
        # Filter out very short or very long strings
        if len(requirement) < 2 or len(requirement) > 200:
            return True
        
        # Filter out strings that are mostly special characters
        special_char_ratio = sum(1 for c in requirement if not (c.isalnum() or c in '.-_[]>=<~!;:')) / len(requirement)
        if special_char_ratio > 0.3:
            return True
        
        return False
    
    def _parse_requirement_string(self, requirement: str) -> Optional[ExpectedPackage]:
        """Parse a requirement string into expected package data."""
        # This is a simplified parser - in practice, we'd use pip's parsing logic
        requirement = requirement.strip()
        
        # Filter out invalid test cases that shouldn't be requirements
        if self._is_invalid_requirement(requirement):
            return None
        
        # Handle editable installs
        editable = False
        if requirement.startswith('-e '):
            editable = True
            requirement = requirement[3:].strip()
        
        # Handle URLs
        url = None
        if any(prefix in requirement for prefix in ['git+', 'http://', 'https://', 'file:']):
            # For URL dependencies, extract package name from egg fragment or URL
            if '#egg=' in requirement:
                parts = requirement.split('#egg=')
                url = parts[0]
                requirement = parts[1]
            else:
                # For now, skip URL-only dependencies without egg names
                return None
        
        # Split on semicolon for environment markers
        environment_marker = None
        if ';' in requirement:
            req_part, marker_part = requirement.split(';', 1)
            requirement = req_part.strip()
            environment_marker = marker_part.strip()
        
        # Extract extras
        extras = []
        if '[' in requirement and ']' in requirement:
            match = re.match(r'([^[]+)\[([^\]]+)\](.*)$', requirement)
            if match:
                requirement = match.group(1) + match.group(3)
                extras = [extra.strip() for extra in match.group(2).split(',')]
        
        # Extract package name and version constraint
        version_operators = ['>=', '<=', '==', '!=', '~=', '>', '<']
        package_name = requirement
        version_constraint = None
        
        for op in sorted(version_operators, key=len, reverse=True):  # Check longer operators first
            if op in requirement:
                parts = requirement.split(op, 1)
                if len(parts) == 2:
                    package_name = parts[0].strip()
                    version_constraint = op + parts[1].strip()
                    break
        
        # Handle multiple constraints (e.g., ">=1.0,<2.0")
        if ',' in requirement and not version_constraint:
            # This is a complex constraint that needs special handling
            parts = requirement.split(',')
            if len(parts) >= 2:
                # Find the package name from the first constraint
                first_constraint = parts[0].strip()
                for op in sorted(version_operators, key=len, reverse=True):
                    if op in first_constraint:
                        package_name = first_constraint.split(op)[0].strip()
                        version_constraint = requirement.replace(package_name, '').strip()
                        break
        
        if not package_name:
            return None
        
        return ExpectedPackage(
            name=package_name,
            version_constraint=version_constraint,
            environment_marker=environment_marker,
            extras=extras,
            url=url,
            editable=editable
        )
    
    def filter_relevant_tests(self, tests: List[StandardizedTestCase]) -> List[StandardizedTestCase]:
        """Filter tests to focus on dependency parsing scenarios."""
        relevant_tests = []
        
        # Categories we care about for dependency parsing
        relevant_categories = {
            TestCategory.BASIC_PARSING,
            TestCategory.COMPLEX_CONSTRAINTS,
            TestCategory.ENVIRONMENT_MARKERS,
            TestCategory.URL_DEPENDENCIES,
            TestCategory.EDITABLE_INSTALLS,
            TestCategory.EXTRAS,
            TestCategory.VERSION_CONSTRAINTS
        }
        
        for test in tests:
            if test.category in relevant_categories:
                relevant_tests.append(test)
        
        # Limit to reasonable number for initial implementation
        # Prioritize by difficulty to get good coverage
        by_difficulty = {}
        for test in relevant_tests:
            difficulty = test.metadata.difficulty
            if difficulty not in by_difficulty:
                by_difficulty[difficulty] = []
            by_difficulty[difficulty].append(test)
        
        # Select balanced sample
        selected_tests = []
        targets = {
            Difficulty.EASY: 15,
            Difficulty.MEDIUM: 20,
            Difficulty.HARD: 10,
            Difficulty.EXPERT: 5
        }
        
        for difficulty, target_count in targets.items():
            if difficulty in by_difficulty:
                available_tests = by_difficulty[difficulty]
                selected_count = min(target_count, len(available_tests))
                selected_tests.extend(available_tests[:selected_count])
        
        return selected_tests