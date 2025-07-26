# Docker Parser Design & Methodology

## Overview

Docker parsing requires a fundamentally different approach from programming language dependencies due to its multi-layered architecture, diverse package managers, and complex CVE mapping requirements.

## Key Challenges

### 1. Multi-Layer Dependency Sources

```dockerfile
# Each introduces different vulnerability types:
FROM ubuntu:20.04                        # Base image vulnerabilities
RUN apt-get install -y nginx            # System package vulnerabilities  
RUN pip install django==3.2             # Python vulnerabilities
RUN npm install express@4.17.1          # Node.js vulnerabilities
COPY --from=builder /app/binary /app/   # Binary vulnerabilities
```

### 2. Version Resolution Complexity

| Type | Challenge | Solution |
|------|-----------|----------|
| Base Images | `ubuntu:20.04` contains 100s of packages | Parse image manifest for exact package versions |
| System Packages | `apt-get install nginx` - version varies by repo | Extract installed version from layer metadata |
| Pinned Versions | `nginx=1.18.0-0ubuntu1.2` | Direct version mapping |
| Latest Tags | `FROM node:latest` | Resolve to specific digest at scan time |

### 3. CVE Mapping Challenges

**Traditional Dependencies:**
```
Package: requests
Version: 2.25.1
CVE: CVE-2023-32681 (direct mapping)
```

**Docker Dependencies:**
```
Package: openssl
Installed via: apt-get (Ubuntu 20.04)
Version: 1.1.1f-1ubuntu2
CVEs: Need to check:
  - Ubuntu Security Notices (USN)
  - Debian Security Advisories
  - Upstream OpenSSL CVEs
  - Distro-specific patches
```

## Proposed Architecture

### 1. Parser Structure

```python
class DockerParser(BaseParser):
    def parse_dockerfile(self, content: str) -> DockerImage:
        """
        Parse Dockerfile into structured format:
        - Base images with digests
        - System packages by installer
        - Language packages by ecosystem
        - Binary/compiled dependencies
        """
        
    def resolve_versions(self, image: DockerImage) -> ResolvedImage:
        """
        Resolve all versions:
        - Base image → manifest → package list
        - System packages → installed versions
        - Dynamic version resolution
        """
        
    def map_vulnerabilities(self, resolved: ResolvedImage) -> List[Vulnerability]:
        """
        Multi-source CVE mapping:
        - OS-specific databases (USN, DSA)
        - Package-specific databases
        - Container-specific CVEs
        """
```

### 2. Layered Parsing Strategy

#### Layer 1: Base Image Analysis
```python
def analyze_base_image(self, from_statement: str) -> BaseImageInfo:
    """
    Extract:
    - Image name and tag
    - Resolve to specific digest
    - Fetch image manifest
    - Extract pre-installed packages
    """
```

#### Layer 2: System Package Extraction
```python
def extract_system_packages(self, run_commands: List[str]) -> List[SystemPackage]:
    """
    Parse package managers:
    - apt/apt-get (Debian/Ubuntu)
    - yum/dnf (RHEL/CentOS)
    - apk (Alpine)
    - zypper (SUSE)
    - pacman (Arch)
    """
```

#### Layer 3: Language Package Integration
```python
def extract_language_packages(self, commands: List[str]) -> List[Package]:
    """
    Reuse existing parsers:
    - Python (pip, poetry, etc.)
    - Node.js (npm, yarn)
    - Ruby (gem)
    - Go (go mod)
    - Java (maven, gradle)
    """
```

### 3. Version Resolution Strategies

#### Strategy 1: Static Analysis (Fast, Less Accurate)
- Parse Dockerfile text only
- Best guess versions from context
- Suitable for quick scans

#### Strategy 2: Build-Time Analysis (Accurate, Requires Build)
- Actually build the Docker image
- Extract exact versions from layers
- Query package databases inside container

#### Strategy 3: Hybrid Approach (Recommended)
- Static analysis for explicitly versioned packages
- Image manifest lookup for base images
- Package repository queries for latest versions
- Build-time verification for critical images

### 4. CVE Mapping Architecture

```python
class DockerCVEMapper:
    def __init__(self):
        self.mappers = {
            'ubuntu': UbuntuSecurityMapper(),    # USN database
            'debian': DebianSecurityMapper(),    # DSA database
            'alpine': AlpineSecurityMapper(),    # Alpine sec-db
            'rhel': RHELSecurityMapper(),        # RHSA database
        }
    
    def map_system_package_cves(self, package: SystemPackage, distro: str) -> List[CVE]:
        """
        Distro-specific CVE mapping:
        1. Check distro security database
        2. Check upstream package CVEs
        3. Consider distro patches
        """
        
    def map_base_image_cves(self, image: str, tag: str) -> List[CVE]:
        """
        Base image vulnerabilities:
        1. Query image scanning databases
        2. Aggregate all package CVEs
        3. Check image-specific issues
        """
```

## Testing Strategy

### 1. Test Categories

#### Base Image Tests
```yaml
test_cases:
  - name: "Ubuntu with specific version"
    dockerfile: "FROM ubuntu:20.04"
    expected_vulnerabilities: [...]
    
  - name: "Alpine minimal"
    dockerfile: "FROM alpine:3.14"
    expected_vulnerabilities: [...]
    
  - name: "Multi-stage with different bases"
    dockerfile: |
      FROM golang:1.17 AS builder
      FROM alpine:3.14
    expected_vulnerabilities: [...]
```

#### Package Installation Tests
```yaml
test_cases:
  - name: "Apt package with version"
    dockerfile: |
      FROM ubuntu:20.04
      RUN apt-get update && apt-get install -y nginx=1.18.0-0ubuntu1.2
    expected_packages:
      - name: nginx
        version: 1.18.0-0ubuntu1.2
        
  - name: "Multiple package managers"
    dockerfile: |
      FROM ubuntu:20.04
      RUN apt-get install -y python3-pip nodejs npm
      RUN pip install requests==2.25.1
      RUN npm install express@4.17.1
```

### 2. Validation Framework

```python
class DockerParserValidator:
    def validate_base_image_parsing(self):
        """Test base image extraction and resolution"""
        
    def validate_package_extraction(self):
        """Test system package parsing accuracy"""
        
    def validate_version_resolution(self):
        """Test version detection strategies"""
        
    def validate_cve_mapping(self):
        """Test CVE mapping accuracy by distro"""
        
    def validate_complex_dockerfiles(self):
        """Test real-world Dockerfile parsing"""
```

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Docker Parser PDR v1.0
- [ ] Basic Dockerfile parsing (FROM, RUN)
- [ ] Test framework setup
- [ ] Simple base image resolution

### Phase 2: Package Extraction (Week 2)
- [ ] apt/apt-get parser
- [ ] yum/dnf parser
- [ ] apk parser
- [ ] Version resolution logic

### Phase 3: CVE Mapping (Week 3)
- [ ] Ubuntu/Debian CVE mapper
- [ ] Alpine CVE mapper
- [ ] RHEL/CentOS CVE mapper
- [ ] Integration with existing language parsers

### Phase 4: Advanced Features (Week 4)
- [ ] Multi-stage build support
- [ ] Build-arg resolution
- [ ] Image layer caching
- [ ] Performance optimization

## Success Metrics

1. **Parsing Accuracy**
   - 95%+ base image detection
   - 90%+ package version resolution
   - Support for top 10 base images

2. **CVE Detection**
   - Match or exceed Trivy/Grype for common images
   - <5% false positive rate
   - Distro-specific patch awareness

3. **Performance**
   - <5s parsing for typical Dockerfile
   - <30s full vulnerability analysis
   - Efficient caching strategy

4. **Coverage**
   - All major Linux distributions
   - All common package managers
   - Multi-stage build support

## Conclusion

Docker parsing requires a multi-layered approach that combines:
1. Sophisticated parsing for various package managers
2. Distro-aware CVE mapping
3. Version resolution strategies
4. Integration with existing language parsers

This design provides a robust foundation for comprehensive Docker vulnerability scanning while acknowledging the unique challenges of container security.