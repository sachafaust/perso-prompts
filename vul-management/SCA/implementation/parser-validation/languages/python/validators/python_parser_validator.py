"""
Python parser validator implementation.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add SCA scanner to path to access our existing parser
sca_path = Path(__file__).parent.parent.parent.parent.parent / "src"
if str(sca_path) in sys.path:
    pass  # Already added
else:
    sys.path.insert(0, str(sca_path))

try:
    # Try relative import first
    from ....common.validator_base import BaseParserValidator
    from ....common.test_format import StandardizedTestCase, ValidationResult, FileType
except ImportError:
    # Fall back to absolute import
    from common.validator_base import BaseParserValidator  
    from common.test_format import StandardizedTestCase, ValidationResult, FileType

try:
    # Import our existing SCA scanner Python parser
    from sca_ai_scanner.parsers.python_parser import PythonDependencyParser
    HAS_SCA_PARSER = True
except ImportError:
    print("Warning: SCA scanner not available. Using mock parser for testing.")
    HAS_SCA_PARSER = False


class MockPythonParser:
    """Mock Python parser for testing when SCA scanner is not available."""
    
    def parse_requirements_txt(self, content: str) -> List[Dict[str, Any]]:
        """Mock requirements.txt parsing."""
        dependencies = []
        for line in content.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Very basic parsing for testing
            dep = {'name': line, 'version': None, 'extras': []}
            
            # Extract package name and version
            if '==' in line:
                parts = line.split('==')
                dep['name'] = parts[0].strip()
                dep['version'] = f"=={parts[1].strip()}"
            elif '>=' in line:
                parts = line.split('>=')
                dep['name'] = parts[0].strip()
                dep['version'] = f">={parts[1].strip()}"
            
            dependencies.append(dep)
        
        return dependencies
    
    def parse_pyproject_toml(self, content: str) -> List[Dict[str, Any]]:
        """Mock pyproject.toml parsing."""
        return []  # Simplified for testing
    
    def parse_setup_py(self, content: str) -> List[Dict[str, Any]]:
        """Mock setup.py parsing."""
        return []  # Simplified for testing


class PythonParserValidator(BaseParserValidator):
    """Validator for Python dependency parsers."""
    
    def __init__(self, parser_name: str = "SCA Python Parser"):
        """
        Initialize Python parser validator.
        
        Args:
            parser_name: Name of the parser being validated
        """
        super().__init__(parser_name)
        
        if HAS_SCA_PARSER:
            self.parser = PythonDependencyParser()
        else:
            self.parser = MockPythonParser()
            print("Using mock parser - results will be limited")
    
    def parse_dependency_file(self, content: str, file_type: str) -> Dict[str, Any]:
        """
        Parse dependency file content using our Python parser.
        
        Args:
            content: File content to parse
            file_type: Type of dependency file
            
        Returns:
            Parsed dependency information in standardized format
        """
        try:
            # Route to appropriate parser method based on file type
            if file_type == FileType.REQUIREMENTS_TXT.value:
                raw_deps = self.parser.parse_requirements_txt(content)
            elif file_type == FileType.PYPROJECT_TOML.value:
                raw_deps = self.parser.parse_pyproject_toml(content)
            elif file_type == FileType.SETUP_PY.value:
                raw_deps = self.parser.parse_setup_py(content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Convert to standardized format
            standardized_packages = []
            for dep in raw_deps:
                std_pkg = self._convert_to_standard_format(dep)
                if std_pkg:
                    standardized_packages.append(std_pkg)
            
            return {
                "packages": standardized_packages,
                "parse_success": True,
                "file_type": file_type
            }
            
        except Exception as e:
            return {
                "packages": [],
                "parse_success": False,
                "error": str(e),
                "file_type": file_type
            }
    
    def _convert_to_standard_format(self, raw_dep: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert raw parser output to standardized format.
        
        Args:
            raw_dep: Raw dependency data from parser
            
        Returns:
            Standardized package format or None
        """
        if not raw_dep.get('name'):
            return None
        
        # Handle different parser output formats
        name = raw_dep.get('name', '').strip()
        if not name:
            return None
        
        # Extract version constraint
        version_constraint = None
        if 'version' in raw_dep and raw_dep['version']:
            version_constraint = str(raw_dep['version']).strip()
        elif 'version_spec' in raw_dep and raw_dep['version_spec']:
            version_constraint = str(raw_dep['version_spec']).strip()
        elif 'constraint' in raw_dep and raw_dep['constraint']:
            version_constraint = str(raw_dep['constraint']).strip()
        
        # Extract environment marker
        environment_marker = None
        if 'environment_marker' in raw_dep and raw_dep['environment_marker']:
            environment_marker = str(raw_dep['environment_marker']).strip()
        elif 'marker' in raw_dep and raw_dep['marker']:
            environment_marker = str(raw_dep['marker']).strip()
        
        # Extract extras
        extras = []
        if 'extras' in raw_dep and raw_dep['extras']:
            if isinstance(raw_dep['extras'], list):
                extras = [str(extra).strip() for extra in raw_dep['extras']]
            elif isinstance(raw_dep['extras'], str):
                # Parse extras string like "[dev,test]"
                extras_str = raw_dep['extras'].strip('[]')
                if extras_str:
                    extras = [extra.strip() for extra in extras_str.split(',')]
        
        # Extract URL
        url = None
        if 'url' in raw_dep and raw_dep['url']:
            url = str(raw_dep['url']).strip()
        
        # Extract editable flag
        editable = bool(raw_dep.get('editable', False))
        
        # Extract hash values
        hash_values = []
        if 'hashes' in raw_dep and raw_dep['hashes']:
            if isinstance(raw_dep['hashes'], list):
                hash_values = [str(h).strip() for h in raw_dep['hashes']]
        elif 'hash' in raw_dep and raw_dep['hash']:
            hash_values = [str(raw_dep['hash']).strip()]
        
        return {
            "name": name,
            "version_constraint": version_constraint,
            "environment_marker": environment_marker,
            "extras": extras,
            "url": url,
            "editable": editable,
            "hash_values": hash_values
        }
    
    def load_test_cases_from_yaml_files(self, test_data_dir: Path) -> List[StandardizedTestCase]:
        """
        Load test cases from YAML files in test data directory.
        
        Args:
            test_data_dir: Directory containing YAML test files
            
        Returns:
            List of loaded test cases
        """
        test_cases = []
        
        if not test_data_dir.exists():
            raise FileNotFoundError(f"Test data directory not found: {test_data_dir}")
        
        yaml_files = list(test_data_dir.glob("*.yaml"))
        print(f"Loading test cases from {len(yaml_files)} YAML files...")
        
        for yaml_file in yaml_files:
            print(f"Loading {yaml_file.name}...")
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split on YAML document separators
                yaml_docs = content.split('---')
                
                for doc in yaml_docs:
                    doc = doc.strip()
                    if not doc or doc.startswith('#'):
                        continue
                    
                    try:
                        test_case = StandardizedTestCase.from_yaml(doc)
                        test_cases.append(test_case)
                    except Exception as e:
                        print(f"Warning: Failed to parse test case in {yaml_file.name}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error loading {yaml_file.name}: {e}")
                continue
        
        print(f"Loaded {len(test_cases)} test cases")
        return test_cases
    
    def run_validation_from_yaml_directory(self, test_data_dir: Path) -> List[ValidationResult]:
        """
        Run validation against test cases loaded from YAML directory.
        
        Args:
            test_data_dir: Directory containing YAML test files
            
        Returns:
            List of validation results
        """
        test_cases = self.load_test_cases_from_yaml_files(test_data_dir)
        return self.run_validation(test_cases)
    
    def compare_packages(self, actual_pkg: Dict[str, Any], expected_pkg) -> List[str]:
        """
        Compare individual package results with Python-specific logic.
        
        Args:
            actual_pkg: Actual package data
            expected_pkg: Expected package data
            
        Returns:
            List of differences
        """
        differences = []
        
        # Check package name (normalize case and whitespace)
        actual_name = str(actual_pkg.get('name', '')).strip().lower()
        expected_name = str(expected_pkg.name).strip().lower()
        
        if actual_name != expected_name:
            differences.append(f"Name mismatch: expected '{expected_pkg.name}', got '{actual_pkg.get('name')}'")
        
        # Check version constraint (handle None values)
        actual_version = actual_pkg.get('version_constraint') 
        expected_version = expected_pkg.version_constraint
        
        if actual_version != expected_version:
            differences.append(
                f"Version constraint mismatch: expected '{expected_version}', got '{actual_version}'"
            )
        
        # Check environment marker
        actual_marker = actual_pkg.get('environment_marker')
        expected_marker = expected_pkg.environment_marker
        
        if actual_marker != expected_marker:
            differences.append(
                f"Environment marker mismatch: expected '{expected_marker}', got '{actual_marker}'"
            )
        
        # Check extras (normalize to sets for comparison)
        actual_extras = set(actual_pkg.get('extras', []))
        expected_extras = set(expected_pkg.extras or [])
        
        if actual_extras != expected_extras:
            differences.append(f"Extras mismatch: expected {expected_extras}, got {actual_extras}")
        
        # Check URL
        actual_url = actual_pkg.get('url')
        expected_url = expected_pkg.url
        
        if actual_url != expected_url:
            differences.append(f"URL mismatch: expected '{expected_url}', got '{actual_url}'")
        
        # Check editable flag
        actual_editable = bool(actual_pkg.get('editable', False))
        expected_editable = bool(expected_pkg.editable)
        
        if actual_editable != expected_editable:
            differences.append(f"Editable flag mismatch: expected {expected_editable}, got {actual_editable}")
        
        return differences