# Parser Validation via Open Source Test Suites - Product Design Requirements (PDR)

## Overview

This PDR defines a systematic approach to validate and improve our dependency parsers by leveraging test suites from established open source projects. By using battle-tested test cases from projects like pip-tools, poetry, and setuptools, we can ensure our parsers handle real-world edge cases correctly while enabling AI coding agents to apply test-driven development principles effectively.

## Background

### Current Challenge
Our dependency parsers need to handle complex real-world scenarios across multiple package ecosystems. While we have basic test coverage, we may be missing edge cases that established tools have already discovered and handle correctly.

### Conversation Summary
During development discussions, we identified that projects like pip-tools have extensive test suites covering numerous edge cases:
- Complex version specifiers (e.g., `package>=1.0,<2.0,!=1.5`)
- Environment markers (e.g., `package; python_version >= "3.8"`)
- URL-based dependencies
- Editable installs (`-e git+https://...`)
- Recursive requirements files
- Platform-specific dependencies

Using these test suites as benchmarks would provide a systematic way to validate our parser quality while aligning with our "only make new mistakes" tenet.

## Goals

### Primary Goals
1. **Comprehensive Parser Validation** - Ensure our parsers handle all real-world edge cases correctly
2. **Test-Driven Improvement** - Enable AI coding agents to systematically improve parsers using TDD
3. **Quality Assurance** - Achieve parser quality on par with industry-standard tools
4. **Knowledge Transfer** - Learn from the collective experience of the open source community

### Success Metrics
- 95%+ compatibility with pip-tools test cases for Python parsing
- 95%+ compatibility with relevant test suites for each supported ecosystem
- Zero regressions when updating parsers
- Documented rationale for any intentional parsing differences

## Technical Requirements

### Functional Requirements

#### Test Suite Integration
1. **Test Extraction**
   - Extract test fixtures from target OSS projects
   - Convert test cases to our testing framework format
   - Maintain attribution and licensing compliance

2. **Parser Validation**
   - Run our parsers against extracted test fixtures
   - Compare outputs with expected results
   - Generate compatibility reports

3. **Gap Analysis**
   - Identify parsing differences
   - Categorize as bugs vs intentional design decisions
   - Create issues for each identified gap

4. **Continuous Validation**
   - Automate test suite synchronization
   - Run validation in CI/CD pipeline
   - Alert on new test failures

### Target Projects for Validation

#### Python Ecosystem
- **pip-tools** - Requirements.txt parsing edge cases
- **poetry** - pyproject.toml parsing validation
- **setuptools** - setup.py and setup.cfg parsing
- **pip** - Core requirements parsing logic
- **pipenv** - Pipfile parsing validation

#### JavaScript Ecosystem
- **npm** - package.json parsing
- **yarn** - yarn.lock parsing
- **pnpm** - pnpm-workspace.yaml parsing

#### Other Ecosystems
- **cargo** - Rust Cargo.toml parsing
- **bundler** - Ruby Gemfile parsing
- **composer** - PHP composer.json parsing

### Implementation Approach

#### Phase 1: Framework Setup
1. Create test harness for running external test suites
2. Implement test case conversion utilities
3. Set up compatibility reporting

#### Phase 2: Python Ecosystem
1. Start with pip-tools as proof of concept
2. Extract and convert test cases
3. Run validation and fix identified issues
4. Expand to other Python tools

#### Phase 3: Other Ecosystems
1. Apply learnings from Python to other languages
2. Prioritize based on usage statistics
3. Maintain ecosystem-specific test suites

### AI Agent Considerations

#### Test-Driven Development Enablement
- Each external test case becomes a TDD opportunity
- AI agents can systematically work through failures
- Clear success criteria (matching expected output)
- Traceable decision history for parsing differences

#### Learning Integration
- Failed tests generate new test cases in our suite
- Document why certain behaviors differ
- Build comprehensive "lessons learned" test file
- Share discoveries across parser implementations

## Non-Functional Requirements

### Performance
- Test validation should complete within CI/CD time limits
- Incremental validation for changed parsers only
- Cached test fixtures to reduce external dependencies

### Maintainability
- Clear mapping between external tests and our test suite
- Version tracking for external test suites
- Automated update notifications

### Documentation
- Compatibility matrix for each parser
- Rationale for intentional differences
- Edge case catalog with examples

## Out of Scope

1. **Modifying External Projects** - We only consume their tests, not contribute back
2. **100% Compatibility** - Some parsing differences may be intentional
3. **Private/Proprietary Test Suites** - Only use publicly available tests

## Risks and Mitigations

### Risk: License Compatibility
**Mitigation**: Carefully review licenses, only use test data (not code), maintain proper attribution

### Risk: Test Suite Changes
**Mitigation**: Version-lock test suites, review changes before updating

### Risk: False Positives
**Mitigation**: Allow for documented intentional differences, focus on functional compatibility

## Implementation Details

### pip-tools Test Suite Analysis

Based on research, pip-tools contains comprehensive test coverage in the following areas:

#### Test Structure
- **Location**: `tests/` directory on GitHub
- **Key Test Files**:
  - `test_resolver.py` - Dependency resolution logic
  - `test_cli_compile.py` - Requirements compilation edge cases
  - `test_repository_pypi.py` - PyPI interaction scenarios
  - `test_sync.py` - Package synchronization tests
  
#### Test Data
- **Location**: `tests/test_data/`
- **Package Examples**:
  - `small_fake_with_deps` - Basic dependency chains
  - `small_fake_with_build_deps` - Build dependencies
  - `small_fake_with_pyproject` - pyproject.toml support
  - `small_fake_with_unpinned_deps` - Version resolution
  
#### Edge Cases Covered
1. **Environment Markers**: `package==1.0; python_version >= "3.8"`
2. **Complex Constraints**: `package>=1.0,<2.0,!=1.5`
3. **URL Dependencies**: Git, HTTP, file:// URLs
4. **Editable Installs**: `-e git+https://...` patterns
5. **Recursive Requirements**: `-r other-requirements.txt`
6. **Extras**: `package[extra1,extra2]`
7. **Pre-releases**: Handling alpha, beta, rc versions
8. **Hash Verification**: Multi-line hash specifications

### Alternative: pip-requirements-parser

Research revealed pip-requirements-parser as a comprehensive alternative:
- Reuses pip's own test suite
- Claims to parse "exactly like pip"
- More extensive edge case coverage
- Actively maintained with pip compatibility

### Test Extraction Strategy

1. **Direct Test Import**
   ```python
   # Clone pip-tools repository
   # Extract test fixtures from tests/test_data/
   # Convert test assertions to our format
   ```

2. **Test Case Categories**
   - Basic parsing (package names, versions)
   - Complex constraints (multiple conditions)
   - Special directives (-e, -r, -f)
   - Environment markers and conditionals
   - URL and VCS references
   - Comments and line continuations

3. **Conversion Process**
   ```python
   # Example conversion
   pip_tools_test = "django>=2.0,<3.0; python_version >= '3.6'"
   our_test = {
       "input": "django>=2.0,<3.0; python_version >= '3.6'",
       "expected": {
           "name": "django",
           "version_spec": ">=2.0,<3.0",
           "environment_marker": "python_version >= '3.6'"
       }
   }
   ```

### Standardized Test Format

All parser validation tests will follow this unified structure:

```yaml
test_case:
  id: "pip-tools-001"
  source: "pip-tools/tests/test_cli_compile.py::test_environment_markers"
  category: "environment_markers"
  input:
    content: "requests>=2.28.0; python_version >= '3.7'"
    file_type: "requirements.txt"
  expected:
    packages:
      - name: "requests"
        version_constraint: ">=2.28.0"
        environment_marker: "python_version >= '3.7'"
        extras: []
  metadata:
    difficulty: "medium"
    edge_case: true
    notes: "Tests Python version-specific dependencies"
```

### Compatibility Reporting Format

```json
{
  "report_version": "1.0",
  "test_date": "2025-01-22",
  "parser": "PythonParser",
  "source_project": "pip-tools",
  "summary": {
    "total_tests": 250,
    "passed": 238,
    "failed": 12,
    "compatibility_score": 95.2
  },
  "categories": {
    "basic_parsing": { "passed": 50, "total": 50 },
    "complex_constraints": { "passed": 45, "total": 48 },
    "environment_markers": { "passed": 38, "total": 42 },
    "url_dependencies": { "passed": 30, "total": 35 }
  },
  "failures": [
    {
      "test_id": "pip-tools-042",
      "category": "complex_constraints",
      "input": "package>=1.0,<2.0,!=1.5.0",
      "expected": "...",
      "actual": "...",
      "error": "Failed to parse exclusion constraint !=1.5.0"
    }
  ],
  "recommendations": [
    "Implement support for exclusion constraints (!=)",
    "Add handling for pre-release version matching"
  ]
}

## Proof of Concept Implementation

### Phase 1: Test Extractor Script

```python
# parser_validation/extractors/pip_tools_extractor.py
import git
import json
import ast
from pathlib import Path

class PipToolsTestExtractor:
    def __init__(self, repo_url="https://github.com/jazzband/pip-tools.git"):
        self.repo_url = repo_url
        self.test_cases = []
    
    def extract_tests(self):
        # Clone repository
        repo = git.Repo.clone_from(self.repo_url, "temp/pip-tools")
        
        # Parse test files
        test_files = Path("temp/pip-tools/tests").glob("test_*.py")
        for test_file in test_files:
            self._parse_test_file(test_file)
        
        return self.test_cases
    
    def _parse_test_file(self, file_path):
        # Extract test cases using AST parsing
        # Convert to standardized format
        pass
```

### Phase 2: Validation Runner

```python
# parser_validation/runner.py
class ParserValidator:
    def __init__(self, parser, test_suite):
        self.parser = parser
        self.test_suite = test_suite
    
    def run_validation(self):
        results = {
            "passed": 0,
            "failed": 0,
            "failures": []
        }
        
        for test in self.test_suite:
            try:
                actual = self.parser.parse(test["input"]["content"])
                expected = test["expected"]
                
                if self._compare_results(actual, expected):
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                    results["failures"].append({
                        "test_id": test["id"],
                        "actual": actual,
                        "expected": expected
                    })
            except Exception as e:
                results["failed"] += 1
                results["failures"].append({
                    "test_id": test["id"],
                    "error": str(e)
                })
        
        return results
```

## Implementation Status

**Status**: 🔨 Design Phase

**Completed**:
1. ✅ Analyzed pip-tools test suite structure
2. ✅ Identified key test files and edge cases
3. ✅ Discovered pip-requirements-parser as alternative
4. ✅ Defined standardized test format
5. ✅ Created compatibility reporting structure

**Next Steps**:
1. Implement proof-of-concept test extractor
2. Create validation runner framework
3. Test with our existing PythonParser
4. Document intentional parsing differences
5. Expand to other package managers

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|---------|
| 1.0 | 2025-01-22 | Initial PDR creation based on development discussion | AI Agent |
| 1.1 | 2025-01-22 | Added implementation details, test formats, and proof of concept | AI Agent |

---

*This PDR follows the AI Agent First philosophy, enabling systematic quality improvement through test-driven development.*