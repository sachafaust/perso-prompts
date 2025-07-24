"""
Standardized test format definitions for parser validation.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum
import yaml
import json


class FileType(Enum):
    """Supported file types for dependency parsing."""
    REQUIREMENTS_TXT = "requirements.txt"
    PYPROJECT_TOML = "pyproject.toml"
    SETUP_PY = "setup.py"
    SETUP_CFG = "setup.cfg"
    PIPFILE = "Pipfile"
    PACKAGE_JSON = "package.json"
    PACKAGE_LOCK_JSON = "package-lock.json"
    YARN_LOCK = "yarn.lock"


class TestCategory(Enum):
    """Categories of test cases for systematic organization."""
    BASIC_PARSING = "basic_parsing"
    COMPLEX_CONSTRAINTS = "complex_constraints"
    ENVIRONMENT_MARKERS = "environment_markers"
    URL_DEPENDENCIES = "url_dependencies"
    EDITABLE_INSTALLS = "editable_installs"
    HASH_VERIFICATION = "hash_verification"
    DEPENDENCY_GROUPS = "dependency_groups"
    VERSION_CONSTRAINTS = "version_constraints"
    EXTRAS = "extras"
    RECURSIVE_REQUIREMENTS = "recursive_requirements"
    COMMENTS_HANDLING = "comments_handling"
    MALFORMED_INPUT = "malformed_input"


class Difficulty(Enum):
    """Test difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class ExpectedPackage:
    """Expected package parsing result."""
    name: str
    version_constraint: Optional[str] = None
    environment_marker: Optional[str] = None
    extras: List[str] = None
    url: Optional[str] = None
    editable: bool = False
    hash_values: List[str] = None
    
    def __post_init__(self):
        if self.extras is None:
            self.extras = []
        if self.hash_values is None:
            self.hash_values = []


@dataclass
class TestInput:
    """Test input data."""
    content: str
    file_type: FileType
    file_path: Optional[str] = None


@dataclass
class TestExpected:
    """Expected test results."""
    packages: List[ExpectedPackage]
    error: Optional[str] = None  # For tests expecting parsing errors
    
    def __post_init__(self):
        if self.packages is None:
            self.packages = []


@dataclass
class TestMetadata:
    """Test case metadata."""
    difficulty: Difficulty
    edge_case: bool
    extraction_date: str
    source_version: str
    notes: Optional[str] = None


@dataclass
class StandardizedTestCase:
    """Standardized test case format for all parser validation."""
    id: str
    source: str  # Original source reference (e.g., "pip-tools/tests/test_cli_compile.py::test_environment_markers")
    category: TestCategory
    input: TestInput
    expected: TestExpected
    metadata: TestMetadata
    
    def to_yaml(self) -> str:
        """Convert test case to YAML format."""
        data = {
            'test_case': {
                'id': self.id,
                'source': self.source,
                'category': self.category.value,
                'input': {
                    'content': self.input.content,
                    'file_type': self.input.file_type.value,
                    'file_path': self.input.file_path
                },
                'expected': {
                    'packages': [
                        {
                            'name': pkg.name,
                            'version_constraint': pkg.version_constraint,
                            'environment_marker': pkg.environment_marker,
                            'extras': pkg.extras,
                            'url': pkg.url,
                            'editable': pkg.editable,
                            'hash_values': pkg.hash_values
                        } for pkg in self.expected.packages
                    ],
                    'error': self.expected.error
                },
                'metadata': {
                    'difficulty': self.metadata.difficulty.value,
                    'edge_case': self.metadata.edge_case,
                    'extraction_date': self.metadata.extraction_date,
                    'source_version': self.metadata.source_version,
                    'notes': self.metadata.notes
                }
            }
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'StandardizedTestCase':
        """Create test case from YAML content."""
        data = yaml.safe_load(yaml_content)['test_case']
        
        input_data = TestInput(
            content=data['input']['content'],
            file_type=FileType(data['input']['file_type']),
            file_path=data['input'].get('file_path')
        )
        
        packages = [
            ExpectedPackage(
                name=pkg['name'],
                version_constraint=pkg.get('version_constraint'),
                environment_marker=pkg.get('environment_marker'),
                extras=pkg.get('extras', []),
                url=pkg.get('url'),
                editable=pkg.get('editable', False),
                hash_values=pkg.get('hash_values', [])
            ) for pkg in data['expected']['packages']
        ]
        
        expected = TestExpected(
            packages=packages,
            error=data['expected'].get('error')
        )
        
        metadata = TestMetadata(
            difficulty=Difficulty(data['metadata']['difficulty']),
            edge_case=data['metadata']['edge_case'],
            extraction_date=data['metadata']['extraction_date'],
            source_version=data['metadata']['source_version'],
            notes=data['metadata'].get('notes')
        )
        
        return cls(
            id=data['id'],
            source=data['source'],
            category=TestCategory(data['category']),
            input=input_data,
            expected=expected,
            metadata=metadata
        )


@dataclass
class ValidationResult:
    """Result of validating a single test case."""
    test_id: str
    passed: bool
    actual_result: Dict[str, Any]
    expected_result: Dict[str, Any]
    differences: List[str]
    error: Optional[str] = None


@dataclass
class CompatibilityReport:
    """Compatibility report for a set of validation tests."""
    report_version: str
    test_date: str
    parser: str
    source_project: str
    summary: Dict[str, Any]
    categories: Dict[str, Dict[str, int]]
    failures: List[Dict[str, Any]]
    recommendations: List[str]
    
    def to_json(self) -> str:
        """Convert report to JSON format."""
        return json.dumps({
            'report_version': self.report_version,
            'test_date': self.test_date,
            'parser': self.parser,
            'source_project': self.source_project,
            'summary': self.summary,
            'categories': self.categories,
            'failures': self.failures,
            'recommendations': self.recommendations
        }, indent=2)