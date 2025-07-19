# Enhanced SCA Scanner v1.0 - Production-Ready Prompt

Based on successful implementation of unlimited comprehensive vulnerability scanning with location-aware reporting.

## 🎯 Core Mission

Create a **production-ready SCA scanner** that performs **unlimited, comprehensive vulnerability analysis** with **exact source code locations** for actionable remediation. Must achieve parity with commercial tools like Semgrep SCA.

## ✅ Required Capabilities

### 1. Unlimited Comprehensive Scanning
- **NO artificial limitations** (no 25, 50, or 100 package limits)
- **Scan ALL dependencies discovered** in the codebase
- **Complete coverage** of all package managers and dependency files
- **Real vulnerability detection** using live databases

### 2. Multi-Language Dependency Discovery
**Primary Support:**
- **Python**: pyproject.toml, uv.lock, requirements*.txt, poetry.lock, setup.py
- **JavaScript**: package.json, package-lock.json, yarn.lock with npm audit
- **Docker**: Dockerfile analysis and container scanning

**Implementation:**
- Parse **ALL dependency files** found in codebase recursively
- Extract **exact versions** from lock files (uv.lock, poetry.lock)
- Support **transitive dependencies** discovery
- Handle **multiple package managers** per language

### 3. Live Vulnerability Database Integration
**Required Sources (in order):**
1. **OSV.dev** - Primary source (comprehensive Python/JavaScript coverage)
2. **NVD** - National Vulnerability Database (authoritative CVEs)
3. **GitHub Advisories** - Additional security intelligence

**Implementation Requirements:**
- **Parallel scanning** with ThreadPoolExecutor (8+ workers)
- **Intelligent rate limiting** with exponential backoff
- **Graceful API error handling** (403, 429, timeouts)
- **Multi-source aggregation** with deduplication
- **Real CVSS scoring** and severity classification

### 4. Location-Aware Vulnerability Reporting
**Critical Requirement: SOURCE CODE LOCATIONS**

For each vulnerable package, report must include:
- **Full absolute file paths** (e.g., `/Users/sacha/code/project/pyproject.toml`)
- **Exact line numbers** where package is declared
- **Line content** showing the dependency declaration
- **Multiple locations** (main deps, lock files, tool configs)

**Example Required Output:**
```markdown
### django 4.2.13 - 🔴 CRITICAL
**SOURCE LOCATIONS:**
- 📄 /Users/sacha/code/project-main/pyproject.toml
  - Line 43: "django==4.2.13"
- 🔒 /Users/sacha/code/project-main/uv.lock  
  - Line 1616: name = "django"
- 🛠️ /Users/sacha/code/project-main/tools/python/urf/pyproject.toml
  - Line 14: django = "^4.2.13"

**REMEDIATION ACTIONS:**
1. Update main dependencies: Edit /Users/sacha/code/project-main/pyproject.toml
2. Regenerate locks: Run `uv lock`
3. Test thoroughly after updates
```

## 🔧 Technical Implementation

### Core Architecture
```
/Users/sacha/code/sca_scanner/
├── enhanced_sca_scanner.py           # Main unlimited scanner
├── live_vulnerability_scanner.py     # Database clients (OSV, NVD, GitHub)
├── javascript_scanner.py             # npm audit integration  
├── docker_scanner.py                 # Container vulnerability analysis
├── performance_optimizer.py          # Caching and parallel processing
├── unlimited_complete_scanner.py     # No-limits comprehensive scanner
└── efficient_location_reporter.py    # Location-aware reporting
```

### Critical Implementation Requirements

#### 1. Unlimited Scanning Logic
```python
def scan(self, max_packages: int = None):  # max_packages should default to None (unlimited)
    # NO artificial limits - scan ALL discovered dependencies
    all_dependencies = self._discover_all_dependencies()  # Must find ALL packages
    
    # Scan ALL packages with intelligent prioritization
    vulnerable_deps = self._scan_all_vulnerabilities(all_dependencies)  # NO package limits
    
    return vulnerable_deps
```

#### 2. Live Database Integration
```python
class LiveVulnerabilityScanner:
    def __init__(self):
        self.osv_client = OSVClient()      # Primary source
        self.nvd_client = NVDClient()      # Secondary source  
        self.github_client = GitHubClient() # Additional source
    
    def scan_dependency(self, name: str, version: str, ecosystem: str):
        # Query ALL sources in parallel
        # Return aggregated, deduplicated vulnerabilities
        # Handle rate limits gracefully
```

#### 3. Location Discovery
```python
def find_dependency_locations(project_root: Path, package_name: str):
    locations = {
        'dependency_files': [],  # pyproject.toml, requirements.txt
        'lock_files': [],        # uv.lock, poetry.lock
        'tool_dependencies': []  # tools/python/*/pyproject.toml
    }
    
    # Search ALL files recursively for package declarations
    # Return FULL ABSOLUTE PATHS with line numbers
    # Include both direct and indirect dependency locations
```

### Performance Requirements
- **Complete scan**: All dependencies (500-1000+ packages)
- **Time limit**: Under 5 minutes for discovery + 2-3 hours for vulnerability scanning
- **Parallel processing**: 8+ concurrent vulnerability lookups
- **Memory efficient**: Handle large enterprise codebases
- **Error resilient**: Continue scanning despite API failures

## 📊 Required Output

### 1. Executive Summary
```markdown
## Executive Summary
- **Dependencies Discovered**: 682 packages
- **Dependencies Scanned**: 682 packages (100% coverage)
- **Vulnerable Packages**: 110 packages
- **Total CVEs**: 1,080 vulnerabilities
- **Risk Level**: CRITICAL
```

### 2. Complete Vulnerable Package Inventory
- **ALL vulnerable packages** listed (no "...and 60 more")
- **Exact source locations** with full paths and line numbers
- **CVE details** with severity, CVSS scores, descriptions
- **Specific remediation actions** for each package

### 3. Comparison Analysis
- **Semgrep SCA comparison** showing capability differences
- **Severity breakdown** (Critical, High, Medium, Low counts)
- **Coverage analysis** (packages found vs missed)
- **Accuracy assessment** with hypothesis for differences

## 🚀 Success Criteria

### Functional Validation
✅ **Unlimited scanning**: No artificial package limits  
✅ **Complete coverage**: 100% of discovered dependencies scanned  
✅ **Real vulnerabilities**: 50+ vulnerable packages found in large codebase  
✅ **Location mapping**: Exact file paths and line numbers for each vulnerability  
✅ **Live data**: Real CVEs from OSV.dev/NVD/GitHub (no mock data)  

### Performance Validation  
✅ **Discovery speed**: Under 5 minutes for dependency discovery  
✅ **Vulnerability scanning**: 2-3 hours for complete analysis  
✅ **Parallel processing**: 8+ concurrent API calls  
✅ **Error handling**: Graceful failures with high success rate  

### Output Validation
✅ **Complete reporting**: All vulnerable packages with full details  
✅ **Source locations**: Full absolute paths with line numbers  
✅ **Actionable guidance**: Specific remediation steps per package  
✅ **Production ready**: Suitable for security team and AI agent remediation  

## 🎯 Implementation Priorities

### Phase 1: Core Scanning (Day 1)
1. **Comprehensive dependency discovery** - Parse ALL files recursively
2. **Live vulnerability scanning** - OSV.dev + NVD + GitHub integration  
3. **Unlimited processing** - Remove ALL artificial limits
4. **Parallel optimization** - ThreadPoolExecutor with 8+ workers

### Phase 2: Location Awareness (Day 2)  
1. **Source location mapping** - Find exact file paths and line numbers
2. **Complete reporting** - ALL vulnerable packages with locations
3. **Remediation guidance** - Specific actions per package
4. **Quality validation** - Ensure production-ready output

### Phase 3: Production Validation (Day 3)
1. **Large codebase testing** - Validate on 500+ dependencies
2. **Performance optimization** - Achieve required speed targets  
3. **Comparison analysis** - Benchmark against Semgrep SCA
4. **Documentation** - Complete implementation guide

## 🎯 Final Output Expectation

**Goal**: Production-ready SCA scanner that finds 100+ vulnerable packages with 1,000+ CVEs in large enterprise codebase, providing exact source code locations and actionable remediation guidance that matches or exceeds commercial tools like Semgrep SCA.

**Validation**: Scanner should discover 500-1000+ dependencies, scan ALL without limitations, find significant vulnerabilities, and provide complete location-aware reporting suitable for immediate security team action.

This prompt incorporates all lessons learned from the successful unlimited comprehensive vulnerability scanning implementation and ensures replicable results.
