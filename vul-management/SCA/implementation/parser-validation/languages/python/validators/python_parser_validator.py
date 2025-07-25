"""
Python parser validator implementation.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add SCA scanner to path to access our existing parser
sca_path = Path(__file__).parent.parent.parent.parent.parent / "src"
if str(sca_path) not in sys.path:
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
    from sca_ai_scanner.parsers.python import PythonParser
    from sca_ai_scanner.core.models import Package, SourceLocation, FileType as SCAFileType
    HAS_SCA_PARSER = True
    print("✅ SCA Python parser loaded successfully")
except ImportError as e:
    print(f"⚠️  Warning: SCA scanner not available ({e}). Using mock parser for testing.")
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
            # Use a temporary directory as root_path for the parser
            import tempfile
            self.temp_root = tempfile.mkdtemp()
            self.parser = PythonParser(self.temp_root)
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
            if HAS_SCA_PARSER:
                # Create a temporary file to parse (SCA parser expects file paths)
                import tempfile
                import os
                
                # Determine file extension based on type
                if file_type == FileType.REQUIREMENTS_TXT.value:
                    suffix = '.txt'
                    filename = 'requirements.txt'
                elif file_type == FileType.PYPROJECT_TOML.value:
                    suffix = '.toml'
                    filename = 'pyproject.toml'
                elif file_type == FileType.SETUP_PY.value:
                    suffix = '.py'
                    filename = 'setup.py'
                elif file_type == FileType.POETRY_LOCK.value:
                    suffix = '.lock'
                    filename = 'poetry.lock'
                elif file_type == FileType.UV_LOCK.value:
                    suffix = '.lock'
                    filename = 'uv.lock'
                else:
                    raise ValueError(f"Unsupported file type: {file_type}")
                
                # Create temporary file with content
                with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as tmp_file:
                    tmp_file.write(content)
                    tmp_file_path = Path(tmp_file.name)
                
                # Rename to proper filename for parser detection
                proper_tmp_path = tmp_file_path.parent / filename
                tmp_file_path.rename(proper_tmp_path)
                
                try:
                    # Parse using SCA parser
                    raw_packages = self.parser.parse_file(proper_tmp_path)
                    
                    # Convert SCA Package objects to standardized format
                    standardized_packages = []
                    for pkg in raw_packages:
                        std_pkg = self._convert_sca_package_to_standard_format(pkg)
                        if std_pkg:
                            standardized_packages.append(std_pkg)
                    
                    return {
                        "packages": standardized_packages,
                        "parse_success": True,
                        "file_type": file_type
                    }
                finally:
                    # Clean up temporary file
                    if proper_tmp_path.exists():
                        os.unlink(proper_tmp_path)
            else:
                # Fall back to mock parser
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
    
    def _convert_sca_package_to_standard_format(self, sca_package) -> Optional[Dict[str, Any]]:
        """
        Convert SCA Package object to standardized format.
        
        Args:
            sca_package: SCA Package object
            
        Returns:
            Standardized package format or None
        """
        if not sca_package or not sca_package.name:
            return None
        
        # Extract version constraint 
        version_constraint = None
        if hasattr(sca_package, 'version') and sca_package.version:
            version_constraint = sca_package.version
        elif hasattr(sca_package, 'version_spec') and sca_package.version_spec:
            version_constraint = sca_package.version_spec
        
        # For our updated parser, we need to extract info from source locations
        # since we temporarily encoded it there
        environment_marker = None
        extras = []
        url = None
        editable = False
        clean_name = sca_package.name
        
        # Check if we have source locations with encoded information
        if hasattr(sca_package, 'source_locations') and sca_package.source_locations:
            for source_loc in sca_package.source_locations:
                if hasattr(source_loc, 'declaration'):
                    declaration = source_loc.declaration
                    
                    # Extract editable flag
                    if declaration.strip().startswith('-e '):
                        editable = True
                    
                    # Extract environment marker (after semicolon)
                    if ';' in declaration:
                        _, marker_part = declaration.split(';', 1)
                        environment_marker = marker_part.strip()
                    
                    # Extract extras [extra1,extra2]
                    import re
                    extras_match = re.search(r'\[([^\]]+)\]', declaration)
                    if extras_match:
                        extras_str = extras_match.group(1)
                        extras = [extra.strip() for extra in extras_str.split(',')]
                    
                    # Extract URL (after @)
                    if ' @ ' in declaration:
                        _, url_part = declaration.split(' @ ', 1)
                        url = url_part.strip()
                    elif 'git+' in declaration or 'http' in declaration:
                        # For editable installs, URL might be directly in declaration
                        if '#egg=' in declaration:
                            url_part = declaration.split('#egg=')[0]
                            if url_part.startswith('-e '):
                                url = url_part[3:].strip()
                            else:
                                url = url_part.strip()
        
        # If no specific fields extracted from SCA package, try legacy approach
        if not environment_marker and hasattr(sca_package, 'environment_marker') and sca_package.environment_marker:
            environment_marker = sca_package.environment_marker
        
        if not extras and hasattr(sca_package, 'extras') and sca_package.extras:
            if isinstance(sca_package.extras, list):
                extras = sca_package.extras
            elif isinstance(sca_package.extras, str):
                # Parse extras string
                extras_str = sca_package.extras.strip('[]')
                if extras_str:
                    extras = [extra.strip() for extra in extras_str.split(',')]
        
        if not url and hasattr(sca_package, 'url') and sca_package.url:
            url = sca_package.url
        
        if not editable and hasattr(sca_package, 'editable'):
            editable = bool(sca_package.editable)
        
        # Extract hash values
        hash_values = []
        if hasattr(sca_package, 'hashes') and sca_package.hashes:
            if isinstance(sca_package.hashes, list):
                hash_values = sca_package.hashes
        
        return {
            "name": clean_name,
            "version_constraint": version_constraint,
            "environment_marker": environment_marker,
            "extras": extras,
            "url": url,
            "editable": editable,
            "hash_values": hash_values
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